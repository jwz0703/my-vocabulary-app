"""Soundtrack for the problem-25 explainer: a 120 BPM synth-pop bed plus sound design,
driven by the cue list that anim.html exports (render.mjs writes it to cues.json).
python3 audio.py cues.json out.wav
"""
import json
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(25)


def T(n):
    return np.arange(n) / SR


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


def osc(f, n, kind='sin'):
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, (n,))) / SR
    if kind == 'sin':
        return np.sin(ph)
    if kind == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'sq':
        return np.sign(np.sin(ph))
    if kind == 'tri':
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1


def env(n, a=.002, d=.1):
    t = T(n)
    return np.minimum(1, t / a) * np.exp(-t / d)


# ------------------------------------------------------------------ one-shots
def kick(punch=1.0):
    n = int(.45 * SR); t = T(n)
    f = 48 + 120 * np.exp(-t / .03)
    x = osc(f, n) * np.exp(-t / .17) * punch
    x += lp(rng.standard_normal(n), 3500) * np.exp(-t / .004) * .35
    return np.tanh(x * 1.8)


def snare():
    n = int(.25 * SR); t = T(n)
    x = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t / .06) * .8
    x += osc(190 * (1 + .3 * np.exp(-t / .01)), n) * np.exp(-t / .05) * .6
    return x


def clap():
    n = int(.3 * SR); t = T(n)
    e = sum(np.exp(-np.clip(t - k * .011, 0, None) / .006) * (t >= k * .011) for k in range(3))
    e += np.exp(-np.clip(t - .033, 0, None) / .09) * (t >= .033)
    return bp(rng.standard_normal(n), 900, 5000) * e * .8


def hat(open_=False):
    n = int((.18 if open_ else .05) * SR)
    return hp(rng.standard_normal(n), 8000) * np.exp(-T(n) / (.06 if open_ else .012))


def boom(dur=2.4):
    n = int(dur * SR); t = T(n)
    x = osc(30 + 70 * np.exp(-t / .08), n) * np.exp(-t / .6)
    x += lp(rng.standard_normal(n), 250) * np.exp(-t / .15) * 1.6
    x += bp(rng.standard_normal(n), 2000, 9000) * np.exp(-t / .04) * .5
    return np.tanh(x * 1.4)


def impact(amp=14):
    g = min(1, amp / 24)
    n = int(1.2 * SR); t = T(n)
    x = osc(40 + 90 * np.exp(-t / .05), n) * np.exp(-t / .3) * g
    x += lp(rng.standard_normal(n), 900) * np.exp(-t / .07) * .9 * g
    x += hp(rng.standard_normal(n), 3000) * np.exp(-t / .03) * .4
    return np.tanh(x * 1.5)


def stamp():
    x = impact(24)
    n = int(.6 * SR); t = T(n)
    metal = sum(osc(f, n) * np.exp(-t / d) for f, d in [(523, .3), (1307, .2), (2093, .12)]) * .25
    x[:n] += metal
    return x


def whoosh(dur, f0=300, f1=5000, curve=1.6):
    n = int(dur * SR); t = T(n)
    noise = rng.standard_normal(n)
    out = np.zeros(n); blk = 512; zi = None
    for s in range(0, n, blk):
        fc = f0 * (f1 / f0) ** (s / n)
        b, a = signal.butter(2, [max(fc * .5, 40) / (SR / 2), min(fc * 1.8, SR / 2.2) / (SR / 2)], 'band')
        if zi is None:
            zi = np.zeros(max(len(a), len(b)) - 1)
        y, zi = signal.lfilter(b, a, noise[s:s + blk], zi=zi)
        out[s:s + blk] = y
    u = t / dur
    return out * np.sin(np.pi * u ** (1 / curve)) ** 2


def riser(dur):
    n = int(dur * SR); u = T(n) / dur
    f = 140 * 2 ** (u * 3.2)
    x = lp(osc(f, n, 'saw') + osc(f * 1.007, n, 'saw'), 3000) * .18
    x += whoosh(dur, 300, 10000, .8) * .9
    return x * u ** 2.2


def pop(n=0):
    """Bubble pop; n steps up a pentatonic scale."""
    scale = [0, 2, 4, 7, 9, 12, 14, 16]
    f0 = midi(72 + scale[n % len(scale)])
    k = int(.18 * SR); t = T(k)
    f = f0 * (.6 + .4 * (1 - np.exp(-t / .012)))
    return osc(f, k) * env(k, .001, .05) + osc(f * 2, k) * env(k, .001, .02) * .3


def tick():
    k = int(.03 * SR)
    return hp(rng.standard_normal(k), 3000) * np.exp(-T(k) / .004) * .7 + osc(2400, k) * np.exp(-T(k) / .006) * .3


def hl(n=0):
    """Highlighter: short swipe + bright chime."""
    k = int(.5 * SR); t = T(k)
    f = midi([76, 79, 83, 86][n % 4])
    x = (osc(f, k) + .4 * osc(f * 2.01, k) + .2 * osc(f * 3, k)) * env(k, .002, .18) * .5
    x[:int(.15 * SR)] += whoosh(.15, 2000, 7000, 1) * .5
    return x


def ding(n=0):
    k = int(1.4 * SR); t = T(k)
    base = [84, 88, 91][n % 3]
    x = np.zeros(k)
    for m, d in [(0, .5), (4, .45), (7, .4), (12, .3)]:
        x += osc(midi(base - 12 + m), k) * env(k, .002, d) * .3
        x += osc(midi(base + m) * 2.76, k) * env(k, .001, d * .2) * .05
    return x


def thud(n=0):
    k = int(.5 * SR); t = T(k)
    x = osc(70 - 10 * n + 60 * np.exp(-t / .03), k) * np.exp(-t / .12)
    x += lp(rng.standard_normal(k), 600) * np.exp(-t / .03) * .7
    return np.tanh(x * 1.5)


def fall(dur):
    k = int(dur * SR); u = T(k) / dur
    f = 1800 * (1 - .75 * u)
    vib = 1 + .01 * np.sin(2 * np.pi * 7 * T(k))
    return osc(f * vib, k) * (np.sin(np.pi * u) ** .5) * .35


def boing(n=0):
    k = int(.7 * SR); t = T(k)
    f0 = 140 if n == 0 else 260
    f = f0 * (1 + .45 * np.exp(-t * 5) * np.sin(2 * np.pi * 9 * t)) * (1 + .6 * np.exp(-t / .05))
    x = osc(f, k) * env(k, .002, .25) + osc(f * 1.5, k, 'tri') * env(k, .002, .12) * .3
    return x


def zap(n=0):
    """Force arrow shooting out: falling-to-rising laser + noise."""
    k = int(.4 * SR); t = T(k)
    f = midi(60 + [0, 7, 12][n % 3]) * (1 + 2 * np.exp(-t / .03))
    x = osc(f, k, 'sq') * env(k, .001, .09) * .25
    x = lp(x, 4000) + whoosh(.4, 500, 6000, 1) * .5
    return x


def glitch():
    k = int(.45 * SR); out = np.zeros(k)
    for s in range(0, k, int(.03 * SR)):
        n2 = int(.03 * SR)
        seg = osc(rng.uniform(200, 2500), n2, 'sq') * .3 if rng.random() < .5 else rng.standard_normal(n2) * .4
        out[s:s + n2] = seg[:len(out[s:s + n2])] * (rng.random() < .8)
    return bp(out, 300, 7000) * np.exp(-T(k) / .25)


def slideup():
    k = int(.5 * SR); u = T(k) / .5
    return osc(300 * 2 ** (u * 1.5), k, 'tri') * np.sin(np.pi * u) * .4 + whoosh(.5, 200, 3000, 1) * .4


def swish(dur):
    return whoosh(dur, 800, 6000, 1.2)


def slide(dur):
    k = int(dur * SR); u = T(k) / dur
    x = osc(220 * 2 ** (u * .9), k, 'saw') * .1 + whoosh(dur, 400, 2500, 1.5) * .6
    return lp(x, 3000) * np.sin(np.pi * u)


def count(n=0):
    k = int(.05 * SR)
    f = 900 + n * 40
    return osc(f, k, 'sq') * np.exp(-T(k) / .01) * .2


def grow(dur, f=1.0):
    k = int(dur * SR); u = T(k) / dur
    x = osc(110 * f * 2 ** (u * 1.5), k, 'saw') + osc(110 * f * 2 ** (u * 1.5) * 1.01, k, 'saw')
    return lp(x, 2500) * .12 * np.sin(np.pi * u * .5 + .2) + whoosh(dur, 300, 5000, 1) * .5


def sparkle():
    out = np.zeros(int(1.6 * SR))
    for i in range(18):
        f = midi(84 + [0, 4, 7, 11, 12, 16, 19][rng.integers(7)])
        k = int(.3 * SR)
        x = osc(f, k) * env(k, .001, .06) * .18
        s = int(rng.uniform(0, 1.2) * SR)
        out[s:s + k] += x
    return out


def swell(dur):
    return whoosh(dur, 6000, 400, 2)[::-1] * .8


def sweep(vals, rate):
    """Tone whose pitch tracks T/W on screen (1x -> ~6x)."""
    vals = np.asarray(vals)
    k = int(len(vals) / rate * SR)
    r = np.interp(T(k), np.arange(len(vals)) / rate, vals)
    f = 220 * r ** .9
    x = osc(f, k, 'saw') * .5 + osc(f * 1.005, k, 'saw') * .5
    x = lp(x, 2500) * .25
    u = T(k) / (k / SR)
    return x * np.minimum(1, u / .05) * np.minimum(1, (1 - u) / .03) * (.6 + .4 * u)


def end_hit():
    x = boom(3.0) * .7
    k = len(x)
    for m in [57, 64, 69, 72, 76]:
        x += osc(midi(m), k, 'tri') * env(k, .005, .9) * .12
    return x


# ------------------------------------------------------------------ music bed
PROG = [[45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62]]   # Am F C G
BAR = 2.0


def music(N, dur):
    bed = np.zeros((N, 2)); side = np.ones(N)
    t = T(N)

    def put(x, t0, pan=0., g=1.):
        i = int(t0 * SR)
        if i >= N:
            return
        x = x[:N - i] * g
        a = (pan + 1) * np.pi / 4
        bed[i:i + len(x), 0] += x * np.cos(a); bed[i:i + len(x), 1] += x * np.sin(a)

    def section(tb):
        # 0 intro, 1 verse, 2 groove, 3 build, 4 drop, 5 halftime, 6 outro
        for s0, s1, k in [(0, 6, 0), (6, 26, 1), (26, 46, 2), (46, 55, 3), (55, 66, 4), (66, 76, 5), (76, 99, 6)]:
            if s0 <= tb < s1:
                return k

    # pad: detuned saws per bar
    nbar = int(np.ceil(dur / BAR))
    pad = np.zeros((N, 2))
    for b in range(nbar):
        ch = PROG[b % 4]; i0 = int(b * BAR * SR); i1 = min(N, int((b + 1) * BAR * SR))
        n = i1 - i0; tt = T(n)
        seg = np.zeros((n, 2))
        for m in ch[1:]:
            for d, c in ((-.12, 0), (.12, 1), (0, 0), (0, 1)):
                seg[:, c] += osc(midi(m) * (1 + d / 100), n, 'saw') * .045
        fade = np.minimum(1, np.minimum(tt / .03, (n / SR - tt) / .03))
        pad[i0:i1] += seg * fade[:, None]
    pad = lp(pad, 1600)
    bed += pad * .8

    beat = .5
    for k in range(int(dur / beat * 4)):
        tb = k * beat / 4; sec = section(tb)
        q = k % 16  # 16th within bar of 4 beats... (one beat = 4 sixteenths)
        on_beat = k % 4 == 0
        bar = int(tb // BAR); ch = PROG[bar % 4]
        if sec in (1, 2, 4) and on_beat:
            if sec != 1 or (k // 4) % 2 == 0:
                put(kick(), tb, 0, .85)
                i = int(tb * SR); n = min(int(.35 * SR), N - i)
                side[i:i + n] *= 1 - .65 * np.exp(-T(n) / .1)
        if sec == 5 and k % 16 == 0:
            put(kick(), tb, 0, .7)
        if sec in (2, 4) and k % 8 == 4:
            put(clap(), tb, 0, .45); put(snare(), tb, 0, .25)
        if sec == 5 and k % 16 == 8:
            put(clap(), tb, 0, .4)
        if sec in (1, 2, 4) and k % 4 == 2:
            put(hat(), tb, .3, .22)
        if sec in (2, 4) and k % 2 == 1:
            put(hat(), tb, -.3, .08)
        if sec == 4 and k % 8 == 6:
            put(hat(True), tb, .2, .12)
        # bass: 8ths on root with octave pops
        if sec in (1, 2, 3, 4) and k % 2 == 0:
            n = int(.22 * SR)
            f = midi(ch[0] - 12 + (12 if (k // 2) % 4 == 3 else 0))
            x = (osc(f, n, 'saw') * .5 + osc(f, n) * .8) * env(n, .003, .15)
            put(lp(x, 900), tb, 0, .38)
        # arp 16ths
        if sec in (2, 3, 4, 5):
            notes = ch[1:] + [ch[1] + 12, ch[2] + 12]
            m = notes[[0, 2, 1, 3, 4, 3, 2, 1][k % 8]] + 12
            n = int(.15 * SR)
            x = (osc(midi(m), n, 'sq') * .3 + osc(midi(m), n, 'tri')) * env(n, .002, .06)
            g = .07 if sec != 4 else .1
            put(lp(x, 5000), tb, .5 * np.sin(k * .7), g)
    # build: snare roll accelerating into the drop at 55.0
    for k in range(64):
        tb = 53.4 + 1.6 * (1 - (1 - k / 64) ** 1.4)
        if tb < 55:
            put(snare(), tb, 0, .12 + .25 * k / 64)

    # duck under the kick
    bed *= (.45 + .55 * side)[:, None]
    # filter sweep in the build, gap before the drop
    i0, i1 = int(46 * SR), int(55 * SR)
    seg = bed[i0:i1]
    u = np.linspace(0, 1, i1 - i0)[:, None]
    bed[i0:i1] = lp(seg, 700) * 1.7 * (1 - u) + seg * u
    gap = 1 - ((t > 54.85) & (t < 55.0))
    bed *= gap[:, None]
    # fade into the end card, then sit quietly
    bed *= np.where(t < 76, 1, np.where(t < 76.3, .6, .35))[:, None]
    return bed


def main(cue_path, out):
    data = json.load(open(cue_path))
    dur = data['dur']; N = int(dur * SR)
    mix = np.zeros((N, 2))

    def put(x, t0, pan=0., g=1.):
        i = int(t0 * SR)
        if i >= N:
            return
        x = x[:N - i] * g
        a = (pan + 1) * np.pi / 4
        mix[i:i + len(x), 0] += x * np.cos(a); mix[i:i + len(x), 1] += x * np.sin(a)

    for c in data['cues']:
        ty, t0, n = c['type'], c['t'], c.get('n', 0)
        pan = rng.uniform(-.25, .25)
        if ty == 'boom': put(boom(), t0, 0, 1.0)
        elif ty == 'impact': put(impact(c.get('amp', 14)), t0, 0, .9)
        elif ty == 'stamp': put(stamp(), t0, 0, 1.0)
        elif ty == 'swell': put(swell(.3), t0, 0, .6)
        elif ty == 'whoosh': put(whoosh(c.get('dur', .5), 250, 6000), t0, 0, .55)
        elif ty == 'riser': put(riser(c['dur']), t0, 0, .55)
        elif ty == 'pop': put(pop(n), t0, pan, .45)
        elif ty == 'tick': put(tick(), t0, pan, .25)
        elif ty == 'hl': put(hl(n), t0, pan, .45)
        elif ty == 'ding': put(ding(n), t0, 0, .55)
        elif ty == 'thud': put(thud(n), t0, -.5 if n == 0 else .5, .8)
        elif ty == 'swish': put(swish(c['dur']), t0, 0, .45)
        elif ty == 'fall': put(fall(c['dur']), t0, 0, .5)
        elif ty == 'boing': put(boing(n), t0, 0, .55)
        elif ty == 'zap': put(zap(n), t0, [0, -.5, .5][n % 3], .5)
        elif ty == 'glitch': put(glitch(), t0, 0, .6)
        elif ty == 'slideup': put(slideup(), t0, .5, .5)
        elif ty == 'slide': put(slide(c['dur']), t0, 0, .55)
        elif ty == 'count': put(count(n), t0, 0, .5)
        elif ty == 'grow': put(grow(c['dur'], c.get('f', 1)), t0, 0, .55)
        elif ty == 'sparkle': put(sparkle(), t0, 0, .6)
        elif ty == 'sweep': put(sweep(c['vals'], c['rate']), t0, 0, .55)
        elif ty == 'end': put(end_hit(), t0, 0, .7)
        else: print('unknown cue', ty)

    # short plate reverb on the effects
    irn = int(1.4 * SR); wet = np.zeros_like(mix)
    for ch in range(2):
        ir = lp(rng.standard_normal(irn) * np.exp(-T(irn) / .35), 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        wet[:, ch] = signal.fftconvolve(mix[:, ch], ir)[:N]
    mix = mix + hp(wet, 250) * .22

    mix += music(N, dur) * .55
    t = T(N)
    mix *= np.minimum(1, t / .01)[:, None]
    mix *= (1 - np.clip((t - (dur - 1.0)) / 1.0, 0, 1) ** 2)[:, None]
    mix = hp(mix, 30)
    mix = np.tanh(mix * 1.2)
    mix /= np.max(np.abs(mix)) / .9
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print('wrote', out, f'{dur}s')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
