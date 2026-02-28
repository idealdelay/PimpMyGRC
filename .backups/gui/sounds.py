"""
GRC Click Sound Effects — programmatic sound generation + async playback.

Synthesizes short WAV sounds in-memory and plays them via `aplay` subprocess.
No external audio files needed.
"""

import io
import math
import random
import struct
import subprocess
import wave

VALID_SOUNDS = ('off', 'sonar', 'click', 'coin', 'laser', 'blip')

_cache = {}


def _generate_wav(sound_type):
    """Generate WAV bytes for the given sound type."""
    sample_rate = 44100

    if sound_type == 'sonar':
        # 800Hz sine, 150ms, exponential decay
        duration = 0.15
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            decay = math.exp(-t * 20)
            val = math.sin(2 * math.pi * 800 * t) * decay
            samples.append(val)

    elif sound_type == 'click':
        # Short white noise burst, 30ms
        duration = 0.03
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / n
            # Sharp attack/decay envelope
            env = 1.0 - t
            val = (random.random() * 2 - 1) * env
            samples.append(val)

    elif sound_type == 'coin':
        # Two-tone ascending (880Hz -> 1320Hz), 120ms
        duration = 0.12
        n = int(sample_rate * duration)
        half = n // 2
        samples = []
        for i in range(n):
            t = i / sample_rate
            freq = 880 if i < half else 1320
            decay = math.exp(-t * 8)
            val = math.sin(2 * math.pi * freq * t) * decay
            samples.append(val)

    elif sound_type == 'laser':
        # Descending frequency sweep (1500Hz -> 200Hz), 200ms
        duration = 0.2
        n = int(sample_rate * duration)
        samples = []
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = 1500 - (1500 - 200) * t
            decay = 1.0 - t * 0.7
            phase += 2 * math.pi * freq / sample_rate
            val = math.sin(phase) * decay
            samples.append(val)

    elif sound_type == 'blip':
        # 1200Hz sine, 60ms, sharp attack/decay
        duration = 0.06
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            t_norm = i / n
            # Envelope: quick attack, quick decay
            env = min(t_norm * 10, 1.0) * (1.0 - t_norm)
            val = math.sin(2 * math.pi * 1200 * t) * env
            samples.append(val)

    else:
        return None

    # Convert to 16-bit PCM WAV
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for s in samples:
            s = max(-1.0, min(1.0, s))
            wf.writeframes(struct.pack('<h', int(s * 32767)))
    return buf.getvalue()


def play(sound_type):
    """Play the given sound type. No-op if 'off' or invalid."""
    if sound_type not in VALID_SOUNDS or sound_type == 'off':
        return
    if sound_type not in _cache:
        wav = _generate_wav(sound_type)
        if wav is None:
            return
        _cache[sound_type] = wav
    wav_data = _cache[sound_type]
    try:
        proc = subprocess.Popen(
            ['aplay', '-q', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.stdin.write(wav_data)
        proc.stdin.close()
        # Don't wait — fire and forget
    except Exception:
        pass


def play_click():
    """Play the configured click sound. Reads config each call."""
    sound_type = get_click_sound()
    play(sound_type)


def get_click_sound():
    """Read click_sound from effects config, return sound type string."""
    try:
        from . import effects
        effects._load()
        val = effects._config.get('click_sound', 'off')
        if val in VALID_SOUNDS:
            return val
    except Exception:
        pass
    return 'off'
