"""LAB ONLY. Grid sweep of mod_amd's settings against the research corpus,
judged by the STRATEGY in AMD-STRATEGY.md (not by the raw verdict alone).

The detector is the one in ../amd-sim.py (a port of webitel/mod_amd 52e6bc6,
checked against real lab calls to within 20 ms), restructured so a whole grid
can be scored at once: mod_amd's state (silence_duration, voice_duration,
words, in_greeting) evolves the same way whatever initial_silence, greeting,
after_greeting_silence, maximum_number_of_words and total_analysis_time are -
those only decide WHEN it stops. So the state is computed once per clip for
each (silence_threshold, between_words_silence), and every stop rule is a
"first frame where ..." lookup. --selfcheck compares this with amd-sim.py's
amd() on random settings (with the one-frame TOOLONG fix noted below).

One correction to amd-sim.py: mod_amd stops with TOOLONG when the samples
counted reach total_analysis_time (`sample_count_limit <= 0`, checked before
the frame is classified), i.e. on the frame ending exactly at that time;
amd-sim.py classified that frame first (`>` instead of `>=`), 20 ms late.

  python3 amd-sweep.py <far-dir> <out-dir> [--selfcheck]
  AVMD_TIMES=<avmd-times.json>  use mod_avmd's real detection times (from
                                avmd-harness/avmd-times.py) instead of assuming
                                every beep is heard 0.25 s in and nothing else is
"""
import itertools, json, os, subprocess, sys, tempfile, wave, importlib.util
import numpy as np

FAR, OUT = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/")
os.makedirs(OUT, exist_ok=True)
SR, FMS = 8000, 20
CLIPS = json.load(open(f"{FAR}/clips.json"))

# ---- strategy constants (AMD-STRATEGY.md section 3) -------------------------
BRIDGE_LAT = 0.3      # verdict -> agent bridged (ESL round trip + bridge), s
AVMD_LAT = 0.25       # avmd fires this long after a beep starts (lab: 0.03-0.23 s)
TCPA_LIMIT = 2.0      # agent within 2 s of the person's completed greeting
BEEP_HOLD = 30.0      # MACHINE: hold for a beep until this long after answer
DROP_LATE = 3.0       # the message must start within this of the last beep's end
WFS_THRESH = 640      # wait_for_silence threshold (= silence_threshold, D2)
WFS_TIMEOUT = 3500    # wait_for_silence timeout: on a line that never goes quiet the
                      # drop starts this long after the avmd event (a deliberate fall-through)

# ---- G.711 u-law round trip (as amd-sim.py) as a lookup table -----------------
def _ul(x):
    BIAS = 0x84; CLIP = 32635
    sign = 0x80 if x < 0 else 0
    if x < 0: x = -x
    x = min(x, CLIP) + BIAS
    exp = 7
    for e in range(7, -1, -1):
        if x & (0x4000 >> (7 - e)) or e == 0: exp = e; break
    mant = (x >> (exp + 3)) & 0x0F
    return ~(sign | (exp << 4) | mant) & 0xFF
def _lu(u):
    u = ~u & 0xFF; sign = u & 0x80; exp = (u >> 4) & 7; mant = u & 0x0F
    x = ((mant << 3) + 0x84) << exp; x -= 0x84
    return -x if sign else x
RT = np.array([_lu(_ul(v)) for v in range(-32768, 32768)], dtype=np.int32)

def load(name, gain_db=0.0, tempo=1.0):
    p = f"{FAR}/{name}.wav"
    if tempo != 1.0:
        q = tempfile.mktemp(suffix=".wav")
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", p, "-af", f"atempo={tempo}",
                        "-ar", "8000", "-ac", "1", "-sample_fmt", "s16", q], check=True)
        p = q
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    if tempo != 1.0: os.unlink(p)
    a = np.clip(np.round(a * 10 ** (gain_db / 20)), -32768, 32767).astype(np.int32)
    return RT[a + 32768]

def scores(a):
    n = len(a) // 160
    return np.abs(a[: n * 160]).reshape(n, 160).sum(1) // 160   # (uint32)(energy / samples)

def wfs_scores(a):
    """wait_for_silence's frame level, as FreeSWITCH 1.10.12 really computes it.
    switch_ivr_wait_for_silence (switch_ivr_play_say.c:2199-2206) does
        energy += abs(data[j++]); j += channels;
    so on a mono call it adds every OTHER sample (and walks past the 160 it was
    given into the unused, zeroed half of the frame buffer) and still divides
    by 160: the level it compares with its threshold is about half of mod_amd's
    for speech and noise, and ~40% for a 1000 Hz tone. This model reproduces
    the lab's eight measured BE-17 drop start times to 20 ms (8.52, 8.52, 8.52,
    9.96, 21.68, 3.50, 5.28, 3.50 s); summing every sample misses three of
    them by 1.4-2.2 s. It is why the lab's 1.2 s beep did not hold the drop
    back (NOTES, "2 rows - vm_beep_1200ms"): to the wait, that beep is quiet."""
    n = len(a) // 160
    return np.abs(a[: n * 160]).reshape(n, 160)[:, ::2].sum(1) // 160

AVMD = json.load(open(os.environ["AVMD_TIMES"]))["times"] if os.environ.get("AVMD_TIMES") else None

def facts(name, tempo=1.0, gain=0.0):
    f = dict(CLIPS[name]); s = 1.0 / tempo
    for k in ("speech_start", "speech_end", "greeting_end", "duration"):
        if k in f: f[k] = f[k] * s
    f["beeps"] = [[b0 * s, b1 * s] for b0, b1 in f["beeps"]]
    # when avmd fires: measured (avmd-replay) or assumed
    if AVMD is not None:
        f["beep_det"] = AVMD[f"{name}|{int(gain)}|{tempo}"]
    else:
        f["beep_det"] = f["beeps"][0][0] + AVMD_LAT if f["beeps"] else None
    return f

# ---- mod_amd state, independent of the stop thresholds ---------------------
def trajectory(sc, st, bws, mwl=100):
    n = len(sc); voiced = sc >= st
    sil_a = np.zeros(n, np.int32); voi_a = np.zeros(n, np.int32); words_a = np.zeros(n, np.int32)
    greet_b = np.zeros(n, bool); init_b = np.zeros(n, bool)
    sil = voice = words = 0; in_word = True; init = True; greet = False
    for k in range(n):
        greet_b[k] = greet; init_b[k] = init
        if not voiced[k]:
            sil += FMS
            if sil >= bws: in_word = False; voice = 0
        else:
            voice += FMS
            if voice >= mwl and not in_word: words += 1; in_word = True
            if voice >= mwl:
                sil = 0
                if not greet: init = False; greet = True
        sil_a[k] = sil; voi_a[k] = voice; words_a[k] = words
    return dict(voiced=voiced, sil=sil_a, voi=voi_a, words=words_a, greet=greet_b, init=init_b)

INF = 10 ** 9
def first(mask):
    i = np.argmax(mask, axis=-1)
    return np.where(mask.any(axis=-1), i, INF)

# stop causes: 0 TOOLONG, 1 INITIALSILENCE, 2 SILENCEAFTERGREETING, 3 MAXWORDS, 4 LONGGREETING
CAUSE = ["TOOLONG", "INITIALSILENCE", "SILENCEAFTERGREETING", "MAXWORDS", "LONGGREETING", "END"]
VERDICT = ["NOTSURE", "NOTSURE", "HUMAN", "MACHINE", "MACHINE", "NOTSURE"]

def grid_verdicts(tr, IS, AGS, N, G, TAT):
    """returns (cause, frame) arrays shaped (IS, AGS, N, G, TAT)"""
    sil, voi, words, voiced = tr["sil"], tr["voi"], tr["words"], tr["voiced"]
    silent = ~voiced; n = len(sil)
    f_is = first(silent & tr["init"] & (sil >= np.array(IS)[:, None]))
    f_ags = first(silent & tr["greet"] & (sil >= np.array(AGS)[:, None]))
    f_n = first(voiced & (words >= np.array(N)[:, None]))
    # maximum_word_length is kept above greeting, so it never fires first (in_greeting
    # is set after min_word_length of voice, long before either is reached)
    f_g = first(voiced & tr["greet"] & (voi >= np.array(G)[:, None]))
    f_t = np.array([int(np.ceil(t / FMS)) - 1 for t in TAT])          # frame on which TOOLONG fires
    f_t = np.where(f_t < n, f_t, INF)
    # priority inside one frame: TOOLONG first (checked before the frame is
    # classified), then MAXWORDS before LONGGREETING; IS/AGS are silent frames only
    key = np.stack(np.broadcast_arrays(
        (f_t * 8 + 0)[None, None, None, None, :],
        (f_is * 8 + 1)[:, None, None, None, None],
        (f_ags * 8 + 1)[None, :, None, None, None],
        (f_n * 8 + 1)[None, None, :, None, None],
        (f_g * 8 + 2)[None, None, None, :, None]), 0).astype(np.int64)
    which = np.argmin(key, 0); kmin = np.min(key, 0)
    frame = kmin // 8
    cause = np.where(frame >= INF, 5, which)
    frame = np.where(frame >= INF, n - 1, frame)
    return cause.astype(np.int8), frame

# ---- wait_for_silence (switch_ivr_play_say.c:2080) from the avmd event ------
_WFS = {}
def wfs_start(sc, t0, hits, timeout_ms=None):
    timeout_ms = timeout_ms or WFS_TIMEOUT
    key = (hash(sc.tobytes()), round(t0, 4), hits, timeout_ms)
    if key not in _WFS: _WFS[key] = _wfs(sc, t0, hits, timeout_ms)
    return _WFS[key]

def _wfs(sc, t0, hits, timeout_ms):
    k = int(np.ceil(t0 * 1000 / FMS)); left = hits; count = timeout_ms // FMS; countdown = 0
    while k < len(sc):
        count -= 1
        if count <= 0: return (k + 1) * FMS / 1000, True
        if countdown:
            countdown -= 1
            if countdown == 0: return (k + 1) * FMS / 1000, False
            k += 1; continue
        if sc[k] < WFS_THRESH:
            left -= 1
            if left == 0: countdown = 25
        else:
            left = hits
        k += 1
    return None, True

def outcome(f, sc, verdict, t_verdict, wfs_hits):
    """what the strategy does with this call: ('agent'|'agent_late'|'drop', detail)"""
    beep_det = f["beep_det"]
    if verdict == "MACHINE":
        if beep_det is not None and beep_det <= BEEP_HOLD:
            return "drop", max(beep_det, 0)
        return "agent_late", max(t_verdict, BEEP_HOLD)
    bridge = t_verdict + BRIDGE_LAT
    if beep_det is not None and beep_det <= bridge:
        return "drop", beep_det
    return "agent", bridge

def judge(f, sc, cause, t_verdict, wfs_hits):
    v = VERDICT[cause]; act, t = outcome(f, sc, v, t_verdict, wfs_hits)
    exp = f["expect"]; ok = True; why = ""
    if exp == "agent":
        if v == "MACHINE": ok, why = False, "MACHINE on a person/line"
        elif act != "agent": ok, why = False, f"{act}"
        elif "speech_end" in f and t_verdict >= f["speech_end"] and t - f["speech_end"] > TCPA_LIMIT:
            ok, why = False, f"agent {t - f['speech_end']:.2f}s after they stopped"
    elif exp in ("drop", "agent_or_drop"):
        if act == "drop" and not f["beeps"]:
            ok, why = False, "drop on a false beep"
        elif act == "drop":
            start, timed_out = wfs_start(sc, t, wfs_hits)
            last_end = f["beeps"][-1][1]
            if start is None: ok, why = False, "drop never started"
            elif start < last_end: ok, why = False, f"drop {last_end - start:.2f}s before the beep ended"
            elif start > last_end + DROP_LATE: ok, why = False, "drop too late"
        elif exp == "drop" and f["beep_det"] is None:
            ok, why = True, "beep not heard: an agent gets it (detector miss, not a setting)"
        elif exp == "drop": ok, why = False, act
    elif exp == "nodrop":
        if act == "drop": ok, why = False, "drop on a false beep (no beep in the audio)"
    return ok, v, act, why

def critical(f, sc, cause, t_verdict, wfs_hits):
    """the failures that hurt a person: MACHINE (held / hung up) or a drop played to them"""
    ok, v, act, why = judge(f, sc, cause, t_verdict, wfs_hits)
    return f["expect"] == "agent" and (v == "MACHINE" or act != "agent")

# ---- the grid ----------------------------------------------------------------
GRID = dict(
    silence_threshold=[512, 640, 768, 896, 1024, 1280, 1536],
    between_words_silence=[150, 250, 400, 500, 600, 700, 800, 900, 1000],
    initial_silence=[2000, 2500, 3000, 3500],
    after_greeting_silence=[700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
    maximum_number_of_words=[3, 4, 5, 6, 8, 10, 12, 99],
    greeting=list(range(1500, 6001, 250)),
    total_analysis_time=list(range(5000, 12001, 500)),
)
ST, BWS, IS, AGS, N, G, TAT = (GRID[k] for k in GRID)
NMAX = max(GRID["total_analysis_time"]) // FMS + 1   # frames mod_amd can ever look at
WFS_HITS = 50   # the drop's quiet-frame count after the beep (see AMD-STRATEGY.md 3.3)

def sweep(variants, must, wfs_hits=WFS_HITS):
    """variants: list of (name, gain, tempo). Returns pass counts per cell."""
    shape = (len(ST), len(BWS), len(IS), len(AGS), len(N), len(G), len(TAT))
    passes = {}; crits = {}; allpass = np.ones(shape, bool)
    for (name, gain, tempo) in variants:
        if name not in passes: passes[name] = np.zeros(shape, np.int8); crits[name] = np.zeros(shape, np.int8)
        a = load(name, gain, tempo); sc = scores(a); wsc = wfs_scores(a); f = facts(name, tempo, gain)
        # the strategy's judgement depends only on (stop cause, stop frame): tabulate it once
        table = np.array([[judge(f, wsc, c, (k + 1) * FMS / 1000, wfs_hits)[0] for k in range(NMAX)]
                          for c in range(len(CAUSE))])
        ctable = np.array([[critical(f, wsc, c, (k + 1) * FMS / 1000, wfs_hits) for k in range(NMAX)]
                           for c in range(len(CAUSE))])
        for i, st in enumerate(ST):
            for j, bws in enumerate(BWS):
                tr = trajectory(sc[:NMAX], st, bws)
                cause, frame = grid_verdicts(tr, IS, AGS, N, G, TAT)
                fr = np.minimum(frame, NMAX - 1)
                ok = table[cause, fr]
                crits[name][i, j] += ctable[cause, fr]
                if name in must: allpass[i, j] &= ok
                passes[name][i, j] += ok
    # between_words_silence must stay below after_greeting_silence
    for j, bws in enumerate(BWS):
        for a, ags in enumerate(AGS):
            if bws >= ags: allpass[:, j, :, a] = False
    return allpass, passes, crits

def detail(name, p, gain=0.0, tempo=1.0, wfs_hits=WFS_HITS):
    a = load(name, gain, tempo); sc = scores(a); wsc = wfs_scores(a); f = facts(name, tempo, gain)
    tr = trajectory(sc[:NMAX], p["silence_threshold"], p["between_words_silence"])
    cause, frame = grid_verdicts(tr, [p["initial_silence"]], [p["after_greeting_silence"]],
                                 [p["maximum_number_of_words"]], [p["greeting"]], [p["total_analysis_time"]])
    c, k = int(cause.flat[0]), int(frame.flat[0]); t = (k + 1) * FMS / 1000
    ok, v, act, why = judge(f, wsc, c, t, wfs_hits)
    # how far from flipping: the state reached before the verdict
    upto = slice(0, k)
    gmask = tr["greet"][upto] & ~tr["voiced"][upto]
    return dict(clip=name, verdict=v, cause=CAUSE[c], t=round(t, 2), action=act, ok=bool(ok), why=why,
                max_voice_ms=int(tr["voi"][upto].max(initial=0)), max_words=int(tr["words"][upto].max(initial=0)),
                max_gap_ms=int(tr["sil"][upto][gmask].max(initial=0)))

if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        spec = importlib.util.spec_from_file_location("sim", os.path.join(os.path.dirname(__file__), "..", "amd-sim.py"))
        os.environ["AUDIO"] = FAR
        sim = importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)
        rng = np.random.default_rng(1); bad = 0; total = 0
        for _ in range(60):
            p = {k: int(rng.choice(v)) for k, v in GRID.items()}
            p.update(min_word_length=100, maximum_word_length=p["greeting"] + 1000, silence_notsure=1)
            for name in CLIPS:
                a = load(name)
                v_sim = sim.amd(list(a), dict(p, total_analysis_time=p["total_analysis_time"] - FMS))
                d = detail(name, p)
                total += 1
                if (v_sim[0], v_sim[1]) != (d["verdict"], d["cause"] if d["cause"] != "END" else "END") or abs(v_sim[2] - d["t"]) > 0.001:
                    bad += 1
                    if bad < 5: print("MISMATCH", name, p, v_sim, d)
        print(f"selfcheck: {total - bad}/{total} identical to amd-sim.py (with TOOLONG one frame earlier)")
        sys.exit(1 if bad else 0)

    # ---- the sweep -----------------------------------------------------------
    GAINS, TEMPOS = [-10, -6, -3, 0, 3, 6], [0.85, 1.0, 1.15]
    names = list(CLIPS); stress = [n for n in names if CLIPS[n]["cls"] == "human_stress"]
    must = [n for n in names if n not in stress]
    t0 = __import__("time").time()
    variants = [(n, g, t) for n in names for g in GAINS for t in TEMPOS]
    nominal = [(n, 0, 1.0) for n in names]
    nom_all, nom_pass, _ = sweep(nominal, must)
    rob_all, rob_pass, rob_crit = sweep(variants, must)
    nv = len(GAINS) * len(TEMPOS)
    stack = np.stack([rob_pass[n] for n in must])               # passes out of nv per clip
    worst = stack.min(0); total = stack.sum(0, dtype=np.int32)
    crit = np.stack([rob_crit[n] for n in must]).sum(0, dtype=np.int32)   # person-harming variant outcomes
    stress_nom = {n: nom_pass[n].astype(bool) for n in stress}
    keys = list(GRID)
    def cell(ix): return {k: GRID[k][i] for k, i in zip(keys, ix)}
    ok = nom_all.copy()
    # neighbourhood: of the 14 one-step neighbours, how many also pass every clip nominally
    nb = np.zeros(ok.shape, np.int8)
    for ax in range(ok.ndim):
        for d in (-1, 1):
            sh = np.roll(ok, d, axis=ax)
            idx = [slice(None)] * ok.ndim; idx[ax] = 0 if d == 1 else -1
            sh[tuple(idx)] = False
            nb += sh
    out = {"cells_total": int(np.prod(ok.shape)), "cells_pass_nominal": int(ok.sum()),
           "cells_pass_all_variants": int((ok & (worst == nv)).sum()), "variants_per_clip": nv,
           "cells_pass_nominal_and_no_person_harmed_in_any_variant": int((ok & (crit == 0)).sum()),
           "stress_clips": stress}
    for n in stress:
        out[f"cells_pass_nominal_with_{n}"] = int((ok & stress_nom[n]).sum())
    # marginal ranges of passing settings
    out["ranges_pass_nominal"] = {k: sorted({GRID[k][i] for i in np.nonzero(ok.any(axis=tuple(a for a in range(ok.ndim) if a != ax)))[0]})
                                   for ax, k in enumerate(keys)}
    # rank: no person harmed in any variant first, then the worst clip's
    # robustness, then how many neighbours also pass, then total robustness
    score = np.where(ok, (1000 - np.minimum(crit, 999)).astype(np.int64) * 10 ** 9
                     + worst.astype(np.int64) * 10 ** 7 + nb.astype(np.int64) * 10 ** 5 + total, -1)
    order = np.argsort(score, axis=None)[::-1][:20]
    out["top"] = []
    for flat in order:
        ix = np.unravel_index(flat, ok.shape)
        out["top"].append(dict(cell(ix), worst_clip_variants=int(worst[ix]), neighbours_passing=int(nb[ix]),
                               total_variant_passes=int(total[ix]), person_harming_variants=int(crit[ix]),
                               weakest={n: int(rob_pass[n][ix]) for n in must if rob_pass[n][ix] < nv}))
    # the best cell for each silence_threshold and for each between_words_silence
    def best_where(axis, i):
        sl = [slice(None)] * ok.ndim; sl[axis] = i
        sub = np.full(score.shape, -1, np.int64); sub[tuple(sl)] = score[tuple(sl)]
        flat = int(np.argmax(sub)); ix = np.unravel_index(flat, ok.shape)
        if sub.flat[flat] < 0: return None
        return dict(cell(ix), worst_clip_variants=int(worst[ix]), neighbours_passing=int(nb[ix]),
                    total_variant_passes=int(total[ix]), person_harming_variants=int(crit[ix]))
    out["best_per_silence_threshold"] = [best_where(0, i) for i in range(len(ST))]
    out["best_per_between_words_silence"] = [best_where(1, j) for j in range(len(BWS))]
    best = out["top"][0]
    if os.environ.get("CHOSEN"):
        # a setting picked by hand from the sweep's top band (AMD-STRATEGY.md 5.2):
        # report its own robustness, margins and clip tables instead of the top one
        ch = json.loads(os.environ["CHOSEN"]); ix = tuple(GRID[k].index(ch[k]) for k in keys)
        best = dict(cell(ix), worst_clip_variants=int(worst[ix]), neighbours_passing=int(nb[ix]),
                    total_variant_passes=int(total[ix]), person_harming_variants=int(crit[ix]),
                    passes_nominal=bool(ok[ix]))
        out["chosen"] = best
    # margins: hold the others at the chosen setting and move one dial; where
    # does it stay right on every clip (nominal) with no person harmed in any variant?
    bix = tuple(GRID[k].index(best[k]) for k in keys)
    good = ok & (crit == 0)
    out["margins"] = {}
    for ax, k in enumerate(keys):
        line = [bix[:ax] + (i,) + bix[ax + 1:] for i in range(len(GRID[k]))]
        out["margins"][k] = {str(GRID[k][i]): ("ok" if good[ix] else ("nominal only" if ok[ix] else "fails"))
                             for i, ix in enumerate(line)}
    # beep-detector misses seen per clip in the variants (not counted against settings)
    if AVMD is not None:
        out["avmd_misses"] = {n: sum(1 for gn in GAINS for t in TEMPOS if CLIPS[n]["beeps"] and AVMD[f"{n}|{gn}|{t}"] is None) for n in names}
        out["avmd_false"] = {n: sum(1 for gn in GAINS for t in TEMPOS if not CLIPS[n]["beeps"] and AVMD[f"{n}|{gn}|{t}"] is not None) for n in names}
    chosen = {k: best[k] for k in keys}
    top = {k: out["top"][0][k] for k in keys}
    # the configs on the table, clip by clip, nominal and at every variant
    CONFIGS = {
        "PR1 as drafted": dict(silence_threshold=640, between_words_silence=250, initial_silence=2500,
                               after_greeting_silence=800, maximum_number_of_words=12, greeting=5000, total_analysis_time=7000),
        "PR1 before D1 (lab D8-tuned)": dict(silence_threshold=640, between_words_silence=250, initial_silence=2500,
                               after_greeting_silence=800, maximum_number_of_words=3, greeting=2500, total_analysis_time=6000),
        "sweep top": top,
        "recommended": chosen,
    }
    out["configs"] = {}
    for label, p in CONFIGS.items():
        rows = []
        for n in names:
            d = detail(n, p)
            vs = [detail(n, p, g, t) for g in GAINS for t in TEMPOS]
            d["variants_ok"] = f"{sum(v['ok'] for v in vs)}/{nv}"
            d["variant_failures"] = sorted({f"{v['verdict']}/{v['cause']}:{v['why']}" for v in vs if not v["ok"]})
            d["expect"] = CLIPS[n]["expect"]; d["stress"] = n in stress
            rows.append(d)
        out["configs"][label] = {"params": p, "rows": rows}
    # the drop's wait after the beep: quiet frames needed, every beep clip and variant
    out["wfs"] = {}
    for hits, tmo in ((10, 5000), (75, 30000), (30, 3000), (40, 3000), (50, 3000), (50, 3500), (60, 3500)):
        res = []
        for n in names:
            if not CLIPS[n]["beeps"]: continue
            for g in GAINS:
                for t in TEMPOS:
                    sc = wfs_scores(load(n, g, t)); f = facts(n, t, g)
                    if f["beep_det"] is None: continue
                    st, to = wfs_start(sc, f["beep_det"], hits, tmo)
                    res.append(dict(clip=n, gain=g, tempo=t, after_last_beep=None if st is None else round(st - f["beeps"][-1][1], 2), timed_out=to))
        good = [r for r in res if r["after_last_beep"] is not None and 0 <= r["after_last_beep"] <= DROP_LATE]
        out["wfs"][f"{hits} quiet frames, timeout {tmo} ms"] = dict(timed_out=sum(r["timed_out"] for r in res), ok=len(good), of=len(res),
                                min_after=min(r["after_last_beep"] for r in res if r["after_last_beep"] is not None),
                                max_after=max(r["after_last_beep"] for r in res if r["after_last_beep"] is not None),
                                failures=sorted({(r["clip"], r["after_last_beep"], r["timed_out"]) for r in res if r not in good})[:12])
    out["seconds"] = round(__import__("time").time() - t0)
    json.dump(out, open(f"{OUT}/sweep.json", "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("cells_total", "cells_pass_nominal", "cells_pass_all_variants", "seconds")}))
