"""Procedural soundtrack for the water reel, synced to the visual timeline in reel.html.
python3 audio.py out.wav
"""
import sys
import numpy as np
from scipy import signal

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)


def T(n):
    return np.arange(n) / SR


def place(buf, x, t0, pan=0.0, gain=1.0):
    """Mix mono x into stereo buf at time t0 with equal-power pan (-1..1)."""
    i = int(t0 * SR)
    if i >= N:
        return
    x = x[: N - i] * gain
    a = (pan + 1) * np.pi / 4
    buf[i:i + len(x), 0] += x * np.cos(a)
    buf[i:i + len(x), 1] += x * np.sin(a)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), 'low')
    return signal.lfilter(b, a, x, axis=0)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), 'high')
    return signal.lfilter(b, a, x, axis=0)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x, axis=0)


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- one-shots
def plink(f0=900, dur=.22, rise=2.2):
    """Water drop: a resonant bubble whose pitch sweeps upward."""
    t = T(int(dur * SR))
    f = f0 * (1 + (rise - 1) * (1 - np.exp(-t / .018)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t / .055) * (1 - np.exp(-t / .0015))
    return np.sin(ph) * env


def kick(dur=.45, punch=1.0):
    t = T(int(dur * SR))
    f = 45 + 110 * np.exp(-t / .035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / .16) * punch
    x += lp(rng.standard_normal(len(t)), 3000) * np.exp(-t / .004) * .3
    return np.tanh(x * 1.6)


def boom(dur=2.2):
    t = T(int(dur * SR))
    f = 28 + 60 * np.exp(-t / .09)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / .55)
    x += lp(rng.standard_normal(len(t)), 220) * np.exp(-t / .12) * 1.5
    return np.tanh(x * 1.3)


def splash(dur=.9):
    t = T(int(dur * SR))
    n = rng.standard_normal(len(t))
    x = bp(n, 900, 7000) * np.exp(-t / .16) * (1 - np.exp(-t / .002))
    crackle = (rng.random(len(t)) < 0.004) * rng.standard_normal(len(t)) * np.exp(-t / .3)
    x += hp(crackle, 2500) * 2
    return x


def whoosh(dur, f0, f1, curve=2.0):
    t = T(int(dur * SR))
    n = rng.standard_normal(len(t))
    u = t / dur
    env = np.sin(np.pi * u ** (1 / curve)) ** 2
    # sweep a bandpass by processing in blocks
    out = np.zeros_like(n)
    blk = 1024
    zi = None
    for s in range(0, len(n), blk):
        fc = f0 * (f1 / f0) ** (s / len(n))
        b, a = signal.butter(2, [max(fc * .6, 30) / (SR / 2), min(fc * 1.6, SR / 2.2) / (SR / 2)], 'band')
        seg = n[s:s + blk]
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, seg, zi=zi)
        out[s:s + blk] = y
    return out * env


def riser(dur):
    t = T(int(dur * SR))
    u = t / dur
    f = 110 * 2 ** (u * 3)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = lp(saw, 2500) * .25 + whoosh(dur, 300, 9000, 1.0) * .8
    return x * u ** 2


def boing(f0, dur=.4):
    t = T(int(dur * SR))
    f = f0 * (1 + .25 * np.exp(-t * 6) * np.sin(2 * np.pi * 18 * t / (2 * np.pi) * 6.28))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / .1) * (1 - np.exp(-t / .002))


# ------------------------------------------------------------------- music
BAR = 2.0
CHORDS = [  # (start, notes)
    (0.0, [57, 60, 64, 67, 71]),    # Am9
    (2.0, [53, 57, 60, 64, 69]),    # Fmaj7
    (4.0, [48, 55, 59, 64, 67]),    # Cmaj7
    (6.0, [55, 59, 62, 64, 71]),    # G6
    (8.0, [57, 60, 64, 67, 71]),    # Am9
    (10.0, [53, 57, 60, 64, 69]),   # Fmaj7
    (12.0, [50, 57, 60, 64, 65]),   # Dm9
    (13.5, [45, 57, 64, 71, 72]),   # A(add9) end
]


def chord_at(t):
    c = CHORDS[0][1]
    for s, notes in CHORDS:
        if t >= s:
            c = notes
    return c


def build_bed():
    bed = np.zeros((N, 2))
    t = T(N)
    # pad: detuned saws, per chord segment
    pad = np.zeros((N, 2))
    for k, (s, notes) in enumerate(CHORDS):
        e = CHORDS[k + 1][0] if k + 1 < len(CHORDS) else DUR
        i0, i1 = int(s * SR), int(e * SR)
        tt = T(i1 - i0)
        seg = np.zeros((len(tt), 2))
        for m in notes[1:]:
            for d, ch in ((-.07, 0), (.07, 1), (0, 0), (0, 1)):
                f = midi(m + 12) * (1 + d / 100 * 3)
                ph = 2 * np.pi * f * tt + rng.random() * 6.28
                seg[:, ch] += (2 * ((ph / (2 * np.pi)) % 1) - 1) * .05
        fade = np.minimum(1, np.minimum(tt / .05, (len(tt) / SR - tt) / .05))
        pad[i0:i1] += seg * fade[:, None]
    pad = lp(pad, 1800, 2)
    pad *= (.35 + .4 * np.clip((t - 2) / 2, 0, 1))[:, None]
    bed += pad

    # kick 4-on-floor from 2.0, sidechain envelope
    side = np.ones(N)
    for b in np.arange(2.0, 13.45, .5):
        if 8.3 <= b < 9.5:
            continue
        place(bed, kick(), b, 0, .9)
        i = int(b * SR)
        n = min(int(.3 * SR), N - i)
        side[i:i + n] *= 1 - .7 * np.exp(-T(n) / .09)
    # sub bass on 8ths (root)
    bass = np.zeros(N)
    for b in np.arange(2.0, 13.45, .25):
        root = chord_at(b)[0]
        f = midi(root - 12 if root > 50 else root)
        n = int(.24 * SR)
        tt = T(n)
        x = np.sin(2 * np.pi * f * tt) * np.exp(-tt / .18) * np.minimum(1, tt / .004)
        i = int(b * SR)
        bass[i:i + n] += x[: N - i] * .28
    bed[:, 0] += bass * side
    bed[:, 1] += bass * side
    bed[:, 0] = bed[:, 0] * (.4 + .6 * side)
    bed[:, 1] = bed[:, 1] * (.4 + .6 * side)

    # water-pluck arpeggio (16ths) from 2.0
    pattern = [0, 2, 1, 3, 4, 3, 2, 1]
    for k, b in enumerate(np.arange(2.0, 13.45, .125)):
        notes = chord_at(b)
        m = notes[1 + pattern[k % 8] % (len(notes) - 1)] + 12
        x = plink(midi(m) * .55, .25, 1.8) * .16
        place(bed, x, b, .5 * np.sin(k * .9), 1.0)
    # hats on offbeats from 4.0
    for b in np.arange(4.25, 13.45, .5):
        n = int(.06 * SR)
        x = hp(rng.standard_normal(n), 7000) * np.exp(-T(n) / .015) * .18
        place(bed, x, b, .3)
    return bed


def main(out):
    mix = np.zeros((N, 2))
    bed = build_bed()

    # underwater: low-pass the music during the caustics chapter
    t = T(N)
    uw = np.clip((t - 5.85) / .15, 0, 1) * (1 - np.clip((t - 7.8) / .26, 0, 1))
    bed_lp = lp(bed, 380, 2) * 1.4
    bed = bed * (1 - uw[:, None]) + bed_lp * uw[:, None]

    # time remap: tape slows with the picture (8.3 -> 9.5), then snaps back
    speed = lambda u: (1 + (0.07 - 1) * np.clip((u - .3) / .2, 0, 1) ** 2 * (3 - 2 * np.clip((u - .3) / .2, 0, 1))) \
        if u < 1.36 else 1.0
    i0, i1 = int(8.0 * SR), int(9.56 * SR)
    m = 8.0 * SR
    remap = np.zeros((i1 - i0, 2))
    for k in range(i1 - i0):
        u = (i0 + k) / SR - 8.0
        m += speed(u)
        j = int(m)
        remap[k] = bed[j]
    xf = np.ones(i1 - i0)
    xf[-int(.08 * SR):] = np.linspace(1, 0, int(.08 * SR))
    seg = bed[i0:i1].copy()
    bed[i0:i1] = remap * xf[:, None] + seg * (1 - xf[:, None])
    # tail of the tape effect is murky, darken it
    bed[i0 + int(.45 * SR):i1] = lp(bed[i0 + int(.45 * SR):i1], 900) * 1.2

    mix += bed * .8

    # ---- sound design hits, panned to the picture
    place(mix, whoosh(.5, 3000, 300, 3)[::-1] * .35, 0.0, 0)              # reverse swell into first drop
    for tt_, x, s in [(.5, 0, 1.0), (1.0, -.66, .5), (1.25, .67, .5), (1.5, .46, .45), (1.84, 0, 1.0)]:
        place(mix, plink(700 + 300 * (1 - s), .3), tt_, x, .7 * s + .2)
    place(mix, boom(), .5, 0, .9)
    place(mix, whoosh(.3, 600, 4000, 1), 1.56, 0, .5)
    place(mix, boom(), 1.84, 0, .8)
    place(mix, splash(.5), 1.84, 0, .25)
    # metaball droplets landing
    for k in range(14):
        place(mix, plink(1100 + 500 * rng.random(), .15, 2.6), 2.18 + k * .022 + rng.random() * .05, rng.uniform(-.7, .7), .25)
    place(mix, whoosh(.45, 200, 1200, 1.5), 3.5, 0, .35)
    place(mix, plink(220, .5, 1.6), 3.95, 0, .7)
    # elastic morph boings
    for k, b in enumerate([4.0, 4.5, 5.0, 5.5]):
        place(mix, boing(midi([57, 60, 64, 69][k])), b, .2 * (k - 1.5), .45)
    place(mix, whoosh(.35, 4000, 250, 1.2), 5.68, 0, .7)
    # bubbles underwater
    for k in range(22):
        place(mix, plink(300 + 500 * rng.random(), .12, 1.5), 6.05 + rng.random() * 1.75, rng.uniform(-.8, .8), .18)
    # breach + splash
    place(mix, whoosh(.3, 300, 6000, 1), 7.78, 0, .5)
    place(mix, splash(1.0), 8.16, 0, .7)
    place(mix, boom(), 8.16, 0, .9)
    place(mix, riser(.45) * .8, 9.12, 0, .6)
    place(mix, kick(punch=1.2), 9.56, 0, .9)
    place(mix, splash(.6), 9.74, 0, .25)
    # staggered tank ticks — a rising scale, one per column
    scale = [57, 59, 60, 62, 64, 65, 67, 69, 71]
    for b, st in [(10.02, .045), (10.5, .035), (11.0, .03)]:
        for i in range(9):
            place(mix, plink(midi(scale[i] + 12) * .6, .2, 1.9), b + i * st, (i - 4) / 4.5, .28)
    place(mix, whoosh(.5, 200, 2500, 1.5), 11.5, 0, .55)
    # vortex riser then drain
    place(mix, riser(1.45), 12.0, 0, .9)
    place(mix, whoosh(.25, 6000, 200, .8), 13.3, 0, .5)
    # end card
    place(mix, plink(600, .5, 2.4), 13.64, 0, 1.0)
    place(mix, boom(3.0), 13.64, 0, 1.0)
    for k in range(10):
        place(mix, plink(midi(76 + [0, 3, 7, 10, 12][k % 5]) * .6, .4, 1.5), 13.8 + k * .06, (k % 2 - .5) * .8, .14)
    place(mix, plink(1200, .2), 14.2, .62, .25)
    place(mix, plink(1300, .2), 14.45, -.6, .2)

    # simple stereo reverb (decaying noise IR)
    irn = int(1.8 * SR)
    ir_t = T(irn)
    wet = np.zeros_like(mix)
    for ch in range(2):
        ir = rng.standard_normal(irn) * np.exp(-ir_t / .45)
        ir = lp(ir, 5000)
        ir /= np.sqrt(np.sum(ir ** 2))
        wet[:, ch] = signal.fftconvolve(mix[:, ch], ir)[:N]
    mix = mix + hp(wet, 200) * .28

    # silence gap before the end-card drop
    gap = 1 - np.clip((t - 13.42) / .03, 0, 1) * (1 - np.clip((t - 13.6) / .03, 0, 1)) * .85
    mix *= gap[:, None]
    # fades
    mix *= np.minimum(1, t / .02)[:, None]
    mix *= (1 - np.clip((t - 14.6) / .4, 0, 1) ** 2)[:, None]

    mix = hp(mix, 32)
    mix = np.tanh(mix * 1.1)
    mix /= np.max(np.abs(mix)) / 0.89
    from scipy.io import wavfile
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1])
