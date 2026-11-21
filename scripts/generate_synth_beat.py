"""Generate a clean, royalty-free lo-fi/synthwave background loop (.mp3) using Python + FFmpeg."""

from __future__ import annotations

import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

SAMPLE_RATE = 44100


def midi_to_hz(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def generate_wav(out_wav: Path, duration: float = 20.0, bpm: float = 104.0) -> None:
    n_samples = int(SAMPLE_RATE * duration)
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Am9 -> Fmaj7 -> Dm9 -> Em7
    chords = [
        (45, [57, 60, 64, 67, 71]),  # A2 bass + Am9
        (41, [53, 57, 60, 64, 69]),  # F2 bass + Fmaj7
        (38, [50, 53, 57, 60, 64]),  # D2 bass + Dm9
        (40, [52, 55, 59, 62, 67]),  # E2 bass + Em7
    ]

    samples = [0.0] * n_samples
    arp_step = beat_sec / 2.0  # 8th-note gentle pluck

    for i in range(n_samples):
        t = i / SAMPLE_RATE
        bar_idx = int(t / bar_sec) % len(chords)
        bar_t = t % bar_sec
        bass_midi, pad_notes = chords[bar_idx]

        # Warm pad (sine + soft 2nd harmonic)
        pad = 0.0
        pad_env = min(1.0, bar_t / 0.25) * min(1.0, (bar_sec - bar_t) / 0.15)
        for note in pad_notes:
            f = midi_to_hz(note)
            pad += 0.14 * math.sin(2.0 * math.pi * f * t) + 0.03 * math.sin(4.0 * math.pi * f * t)
        pad *= pad_env * 0.25

        # Sub bass on beats 1 and 3
        beat_pos = (t % (beat_sec * 2.0))
        bass_env = math.exp(-3.2 * beat_pos)
        bass_f = midi_to_hz(bass_midi)
        bass = 0.28 * bass_env * math.sin(2.0 * math.pi * bass_f * t)

        # Gentle 8th-note arp pluck
        arp_idx = int(t / arp_step) % len(pad_notes)
        arp_t = t % arp_step
        arp_env = math.exp(-9.0 * arp_t)
        arp_f = midi_to_hz(pad_notes[arp_idx] + 12)
        arp = 0.10 * arp_env * math.sin(2.0 * math.pi * arp_f * t)

        # Soft muted kick on every beat
        kick_t = t % beat_sec
        kick_env = math.exp(-18.0 * kick_t)
        kick_freq = 52.0 + 75.0 * math.exp(-35.0 * kick_t)
        kick = 0.22 * kick_env * math.sin(2.0 * math.pi * kick_freq * kick_t)

        # Master fade in/out
        fade = min(1.0, t / 0.6) * min(1.0, max(0.0, (duration - t) / 1.5))
        mix = (pad + bass + arp + kick) * fade * 0.75
        samples[i] = max(-0.95, min(0.95, mix))

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        raw = struct.pack("<" + "h" * n_samples, *(int(s * 32767) for s in samples))
        wf.writeframes(raw)


def main() -> None:
    assets_audio = Path(__file__).resolve().parent.parent / "assets" / "audio"
    assets_audio.mkdir(parents=True, exist_ok=True)
    out_mp3 = assets_audio / "synth_tech_loop.mp3"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_wav = Path(tmpdir) / "loop.wav"
        generate_wav(tmp_wav, duration=20.0)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_wav), "-c:a", "libmp3lame", "-b:a", "192k", str(out_mp3)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print(f"Generated: {out_mp3}")


if __name__ == "__main__":
    main()
