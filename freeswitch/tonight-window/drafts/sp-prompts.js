// Secure card entry prompts: AWS Polly (neural) -> 8 kHz mono 16-bit WAV.
// Run INSIDE the API container (it has the AWS keys and these packages):
//   sudo docker compose -f .deploy/compose.yml exec -T app node - < /tmp/sp-prompts.js
// It never prints a key. It prints: a Polly permission check, one line per
// file, 13 listen links and one download link (30 minutes each), and the
// sha256 of the bundle.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");
const { SignatureV4 } = require("@smithy/signature-v4");
const { HttpRequest } = require("@smithy/protocol-http");
const { Sha256 } = require("@aws-crypto/sha256-js");

const REGION = process.env.POLLY_REGION || process.env.AWS_REGION || "us-east-2";
const VOICE = process.env.POLLY_VOICE || "Joanna";
const OUT = "/tmp/sp-prompts/secure_payment";
const HOST = process.env.POLLY_HOST || `polly.${REGION}.amazonaws.com`;
const PROTO = process.env.POLLY_PROTO || "https:";
const DRY = process.env.DRY === "1"; // test mode: no S3 upload

// File names are the ones scripts/secure_payment.lua plays. No prompt ever
// reads a digit back.
const PROMPTS = {
  "payment_intro.wav":
    "You're now on our secure payment line. Your agent can't hear the numbers you press, and they are not recorded. " +
    "Use your phone's keypad. You can press star at any time to go back to your agent.",
  "enter_card_number.wav":
    "Please enter your card number. If it has fewer than sixteen digits, press pound at the end.",
  "enter_expiry.wav":
    "Please enter the expiration date as four digits: two for the month, then two for the year.",
  "enter_cvv.wav": "Please enter the three digit security code on the back of your card.",
  "enter_cvv_amex.wav": "Please enter the four digit security code printed on the front of your card.",
  "enter_zip.wav": "Please enter the five digit ZIP code of your billing address.",
  "invalid_try_again.wav": "Sorry, that entry wasn't valid. Let's try that again.",
  "one_moment.wav": "Thank you. One moment while we securely check your card.",
  "payment_captured.wav": "Thank you. Your card details have been received securely.",
  "card_not_accepted_try_again.wav":
    "Sorry, that card couldn't be accepted. Please check your details, and enter the card number again.",
  "unable_to_process.wav": "Sorry, we're unable to take your card details right now.",
  "returning_to_agent.wav": "Returning you to your agent now.",
  "agent_unavailable.wav": "Sorry, your agent is no longer on the line. Please call us back. Goodbye.",
};

const credentials = {
  accessKeyId: process.env.AWS_ACCESS_KEY || process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_KEY || process.env.AWS_SECRET_ACCESS_KEY,
};
if (!credentials.accessKeyId || !credentials.secretAccessKey) {
  console.error("STOP: no AWS keys in this container's environment");
  process.exit(2);
}
const signer = new SignatureV4({ service: "polly", region: REGION, credentials, sha256: Sha256 });

async function polly(method, pathname, query, body) {
  const req = new HttpRequest({
    protocol: PROTO, hostname: HOST, method, path: pathname, query,
    headers: { host: HOST, ...(body ? { "content-type": "application/json" } : {}) },
    body,
  });
  const signed = await signer.sign(req);
  const qs = query ? "?" + new URLSearchParams(query).toString() : "";
  const res = await fetch(`${PROTO}//${HOST}${pathname}${qs}`, {
    method, headers: signed.headers, body,
  });
  const buf = Buffer.from(await res.arrayBuffer());
  if (!res.ok) {
    // AWS error bodies name the action and the reason, never the key.
    throw new Error(`Polly ${method} ${pathname} -> HTTP ${res.status}: ${buf.toString("utf8").slice(0, 300)}`);
  }
  return buf;
}

function wav8k(pcm) {
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + pcm.length, 4); h.write("WAVE", 8);
  h.write("fmt ", 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22);
  h.writeUInt32LE(8000, 24); h.writeUInt32LE(16000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34);
  h.write("data", 36); h.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([h, pcm]);
}

(async () => {
  // 1. Permission check (read-only).
  try {
    const voices = JSON.parse((await polly("GET", "/v1/voices", { Engine: "neural", LanguageCode: "en-US" })).toString());
    const ok = (voices.Voices || []).some((v) => v.Id === VOICE);
    console.log(`polly: allowed in ${REGION}; neural voice ${VOICE} ${ok ? "available" : "NOT available"}`);
    if (!ok) process.exit(3);
  } catch (e) {
    console.error(`STOP: Polly is not usable with the API's AWS key (access key id ending ${String(credentials.accessKeyId).slice(-4)}): ${e.message}. Use the fallback in the runbook.`);
    process.exit(4);
  }

  // 2. Synthesize each prompt as 8 kHz PCM and wrap it in a WAV header.
  fs.rmSync("/tmp/sp-prompts", { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });
  for (const [file, text] of Object.entries(PROMPTS)) {
    const ssml = `<speak><prosody rate="95%">${text}</prosody></speak>`;
    const body = JSON.stringify({
      Engine: "neural", LanguageCode: "en-US", VoiceId: VOICE,
      OutputFormat: "pcm", SampleRate: "8000", TextType: "ssml", Text: ssml,
    });
    const pcm = await polly("POST", "/v1/speech", undefined, body);
    fs.writeFileSync(path.join(OUT, file), wav8k(pcm));
    const secs = (pcm.length / 16000).toFixed(1);
    // 3. Check the format with ffprobe (in the API image), when present.
    const p = spawnSync("ffprobe", ["-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels",
      "-of", "csv=p=0", path.join(OUT, file)], { encoding: "utf8" });
    const fmt = p.status === 0 ? p.stdout.trim() : "ffprobe unavailable";
    console.log(`made ${file}  ${secs}s  [${fmt}]`);
  }

  // 4. Bundle.
  const tgz = "/tmp/sp-prompts.tgz";
  const t = spawnSync("tar", ["czf", tgz, "-C", "/tmp/sp-prompts", "secure_payment"]);
  if (t.status !== 0) throw new Error("tar failed");
  const sum = crypto.createHash("sha256").update(fs.readFileSync(tgz)).digest("hex");
  console.log(`bundle sha256: ${sum}`);
  if (DRY) return;

  // 5. Upload to the app's bucket under ops/ and print 30-minute links.
  const { S3Client, PutObjectCommand, GetObjectCommand } = require("@aws-sdk/client-s3");
  const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
  const s3 = new S3Client({ region: process.env.AWS_REGION, credentials });
  const Bucket = process.env.AWS_S3_BUCKET;
  const prefix = `ops/fs-window/${new Date().toISOString().slice(0, 10)}`;
  const put = async (Key, file, ContentType) =>
    s3.send(new PutObjectCommand({ Bucket, Key, Body: fs.readFileSync(file), ContentType }));
  const link = (Key) => getSignedUrl(s3, new GetObjectCommand({ Bucket, Key }), { expiresIn: 1800 });
  console.log("\nLISTEN (open each in a browser, 30 minutes):");
  for (const file of Object.keys(PROMPTS)) {
    const Key = `${prefix}/${file}`;
    await put(Key, path.join(OUT, file), "audio/wav");
    console.log(`${file}\n  ${await link(Key)}`);
  }
  const Key = `${prefix}/sp-prompts.tgz`;
  await put(Key, tgz, "application/gzip");
  console.log(`\nDOWNLOAD FOR THE FREESWITCH BOX (30 minutes):\n${await link(Key)}`);
  console.log(`\nS3 prefix to delete afterwards: s3://${Bucket}/${prefix}/`);
})().catch((e) => {
  console.error(`STOP: ${e.message}`);
  process.exit(1);
});
