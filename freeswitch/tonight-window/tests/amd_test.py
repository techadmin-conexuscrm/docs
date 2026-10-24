"""amd.conf.xml must not call a real person a MACHINE.

argv: path/to/autoload_configs/amd.conf.xml   Exit 0 = pass.

The verdict is decided entirely by the arithmetic in webitel/mod_amd at the
pinned SHA 52e6bc69 and the numbers in amd.conf.xml, so it can be checked
without FreeSWITCH. amd_handle_voiced_frame / amd_handle_silence_frame below
are a line-for-line port of that file (frame_ms = 20, as for 8 kHz / 160
sample frames):

  * voice_duration accumulates across a WHOLE utterance. Only a silence of
    between_words_silence or more resets it, so a sentence said without real
    pauses is one long "greeting";
  * a word is counted when voice comes back after such a silence, so the
    first chunk is never counted and N chunks give N-1 words;
  * MACHINE fires on maximum_word_length, on maximum_number_of_words and on
    greeting; HUMAN fires on after_greeting_silence; NOTSURE on
    initial_silence (silence_notsure) and on total_analysis_time.

Each case below is an answer as (voiced ms, silence ms) chunks. The human
cases are what a person actually does on the phone; none of them may come
back MACHINE. Under the strategy (docs freeswitch/lab/research/
AMD-STRATEGY.md) MACHINE no longer plays anything by itself - only the
mod_avmd beep does - but it still sends the call down the voicemail path:
held up to 30 s for a beep that never comes, or hung up on when no drop is
allowed. On a person that is an abandoned call. The machine cases are
voicemail greetings and must still be caught, or enabling AMD buys nothing.
The config-level checks are the strategy's own limits: the 2-second rule
(after_greeting_silence + bridge), an analysis window long greetings can
finish in, and maximum_word_length kept above greeting.
"""
import sys
import xml.etree.ElementTree as ET

FRAME_MS = 20


def verdict(p, chunks):
    """Returns (amd_result, amd_cause, ms of audio analysed)."""
    silence_duration = voice_duration = words = 0
    in_initial_silence, in_greeting, in_word = 1, 0, 1   # vad->state = VAD_STATE_IN_WORD
    analysed = 0
    limit = p["total_analysis_time"]
    for kind, ms in chunks:
        for _ in range(int(ms) // FRAME_MS):
            if limit and analysed >= limit:
                return "NOTSURE", "TOOLONG", analysed
            analysed += FRAME_MS
            if kind == "s":
                silence_duration += FRAME_MS
                if silence_duration >= p["between_words_silence"]:
                    in_word = 0
                    voice_duration = 0
                if in_initial_silence and silence_duration >= p["initial_silence"]:
                    return ("NOTSURE" if p["silence_notsure"] > 0 else "MACHINE",
                            "INITIALSILENCE", analysed)
                if silence_duration >= p["after_greeting_silence"] and in_greeting:
                    return "HUMAN", "SILENCEAFTERGREETING", analysed
            else:
                voice_duration += FRAME_MS
                if voice_duration >= p["min_word_length"] and not in_word:
                    words += 1
                    in_word = 1
                if voice_duration >= p["maximum_word_length"]:
                    return "MACHINE", "MAXWORDLENGTH", analysed
                if words >= p["maximum_number_of_words"]:
                    return "MACHINE", "MAXWORDS", analysed
                if in_greeting and voice_duration >= p["greeting"]:
                    return "MACHINE", "LONGGREETING", analysed
                if voice_duration >= p["min_word_length"]:
                    silence_duration = 0
                if voice_duration >= p["min_word_length"] and not in_greeting:
                    in_initial_silence = 0
                    in_greeting = 1
    return "NOTSURE", "TOOLONG", analysed


def talk(*pairs):
    """("hello", 600, 150, ...) -> alternating voiced/silent chunks, then 3 s quiet."""
    out = []
    for i, ms in enumerate(pairs):
        out.append(("v" if i % 2 == 0 else "s", ms))
    out.append(("s", 3000))
    return out


# What a person does. Numbers are speech timings, not lab TTS: an unhurried
# "Hello, this is John speaking, who's calling please?" is about 2.6-3 s of
# voiced audio, and the gaps inside a spoken phrase are 80-200 ms, well under
# between_words_silence.
PEOPLE = {
    "hello": talk(600),
    "hello, pause, yes?": talk(500, 400, 450),
    # one breath, no real pause anywhere: one long stretch of voice
    "sentence in one breath": talk(400, 120, 500, 100, 600, 150, 450, 120, 700),
    # the same sentence said in phrases, with real pauses between them
    "sentence in phrases": talk(700, 300, 600, 320, 500, 280, 650, 300, 550),
    # someone who keeps going: seven phrases before they stop
    "talkative": talk(600, 300, 500, 300, 550, 300, 600, 300, 500, 300, 650, 300, 600),
    # a fast talker: short phrases with the shortest gaps that still count
    "fast talker": talk(*([350, 280] * 10)),
    # a slow talker, one 4 s breath: the most voice any person in the AMD
    # research corpus reached (3.86 s, slowed and turned up)
    "slow talker, one breath": talk(*([480, 120] * 7 + [500])),
    # "Hello? ... Hello? ... Is anyone there?" into dead air, 0.8-1.1 s apart:
    # every gap is a "word" at a short between_words_silence (MAXWORDS at 3)
    "hello, hello, anyone there?": talk(450, 1100, 450, 800, 900),
    # answers and says nothing
    "silent": [("s", 4000)],
    # a noisy line: every frame below silence_threshold counts as silence
    "noisy line": [("s", 4000)],
}

# Voicemail greetings read without a real pause in them. mod_amd sees one
# unbroken stretch of voice, which is the only thing it can tell apart from
# a person, so these must still come back MACHINE.
MACHINES = {
    "7 s greeting, no real pauses": talk(*([800, 120] * 7)),
    "19 s greeting": talk(*([900, 150] * 18)),
    # A carrier's default greeting: sentences with ordinary 0.4 s pauses
    # between them, ~11 s. At between_words_silence 250 every pause reset
    # voice_duration, so this never reached `greeting` (NOTSURE/TOOLONG):
    # the fault behind every red mailbox row of the fourth and fifth lab
    # passes. It must be caught now.
    "carrier greeting, sentences 0.4 s apart": talk(*([1500, 400] * 6 + [1500])),
    # three sentences 0.45 s apart, words with 150-200 ms gaps inside them
    # (about 11 s, the shape of vm_real_long in the research corpus)
    "11 s greeting, three sentences": talk(*([300, 150] * 9 + [300, 450] + [300, 180] * 9 + [300, 450] + [300, 200] * 9 + [300])),
}

# Greetings mod_amd cannot tell from a person: read as separate sentences
# with pauses long enough to look like a person who stopped, or too short to
# reach `greeting`. Reported for the record, not failed: a missed machine
# costs an agent a few seconds, a wrong MACHINE abandons a live customer.
# Under the strategy their beep still gets them the message.
MISSED_OK = {
    "7 s greeting, pauses between sentences": talk(*([700, 300] * 7)),
}


def main():
    root = ET.parse(sys.argv[1]).getroot()
    p = {e.get("name"): int(e.get("value"))
         for e in root.iter("param") if (e.get("value") or "").isdigit()}
    for k in ("greeting", "after_greeting_silence", "between_words_silence",
              "maximum_number_of_words", "maximum_word_length", "min_word_length",
              "initial_silence", "total_analysis_time", "silence_notsure"):
        if k not in p:
            print("FAIL amd.conf.xml has no %s" % k)
            sys.exit(1)

    fails = []
    # The 2-second rule (47 CFR 64.1200(a)(7)): an agent within 2 s of the
    # end of a person's greeting. mod_amd needs after_greeting_silence of
    # quiet to say HUMAN and the bridge takes about 0.3 s more.
    if p["after_greeting_silence"] + 300 > 2000:
        fails.append("after_greeting_silence %d + 300 ms bridge is over the 2 s the law allows"
                     % p["after_greeting_silence"])
    # Long greetings reach 5 s of voice at 7.8-10 s after answer (research
    # corpus): below 10000 they are cut off as NOTSURE before they can be.
    if p["total_analysis_time"] < 10000:
        fails.append("total_analysis_time %d is under 10000: long greetings never reach `greeting`"
                     % p["total_analysis_time"])
    if p["maximum_word_length"] <= p["greeting"]:
        fails.append("maximum_word_length must stay above greeting (else it is the same rule under another name)")
    for name, chunks in PEOPLE.items():
        r, cause, ms = verdict(p, chunks)
        print("  person   %-28s -> %-7s %-20s at %d ms" % (name, r, cause, ms))
        if r == "MACHINE":
            fails.append("a person answering %r is reported MACHINE/%s at %d ms: a campaign "
                         "would play a recorded message at them and drop the call" % (name, cause, ms))
    for name, chunks in MACHINES.items():
        r, cause, ms = verdict(p, chunks)
        print("  machine  %-28s -> %-7s %-20s at %d ms" % (name, r, cause, ms))
        if r != "MACHINE":
            fails.append("a voicemail greeting (%s) is reported %s/%s: AMD catches nothing"
                         % (name, r, cause))
    for name, chunks in MISSED_OK.items():
        r, cause, ms = verdict(p, chunks)
        print("  missed   %-28s -> %-7s %-20s at %d ms (known, and the safe direction)"
              % (name, r, cause, ms))
        if r == "MACHINE":
            print("    (now caught; MISSED_OK can be tightened)")
    for f in fails:
        print("FAIL " + f)
    print("amd_test: %d people, %d machines, %d known misses, %d failed"
          % (len(PEOPLE), len(MACHINES), len(MISSED_OK), len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
