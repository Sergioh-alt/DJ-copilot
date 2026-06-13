"""
DJ Copilot AI — Synthetic Audio Generator
Creates example WAV files for testing without needing real music.
Generates Techno, Reggaetón, and House patterns using pure synthesis.
"""
import numpy as np
import os


def _make_kick(sr: int, duration: float = 0.15) -> np.ndarray:
    """Synthesize a kick drum."""
    t = np.linspace(0, duration, int(sr * duration), False)
    freq_sweep = 150 * np.exp(-t * 30) + 40
    phase = np.cumsum(2 * np.pi * freq_sweep / sr)
    kick = np.sin(phase) * np.exp(-t * 15)
    return kick * 0.8


def _make_hihat(sr: int, duration: float = 0.05) -> np.ndarray:
    """Synthesize a hi-hat."""
    samples = int(sr * duration)
    noise = np.random.randn(samples)
    envelope = np.exp(-np.linspace(0, 10, samples))
    return noise * envelope * 0.3


def _make_bass_note(sr: int, freq: float, duration: float = 0.25) -> np.ndarray:
    """Synthesize a bass note."""
    t = np.linspace(0, duration, int(sr * duration), False)
    wave = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
    envelope = np.exp(-t * 3)
    return wave * envelope * 0.5


def _make_pad(sr: int, freq: float, duration: float = 2.0) -> np.ndarray:
    """Synthesize a pad/chord sound."""
    t = np.linspace(0, duration, int(sr * duration), False)
    wave = (np.sin(2 * np.pi * freq * t) +
            0.5 * np.sin(2 * np.pi * freq * 1.5 * t) +
            0.3 * np.sin(2 * np.pi * freq * 2 * t))
    # Smooth envelope
    attack = np.minimum(t / 0.5, 1.0)
    release = np.minimum((duration - t) / 0.5, 1.0)
    envelope = attack * release
    return wave * envelope * 0.2


def generate_techno_example(output_path: str, sr: int = 22050, duration_sec: float = 30.0):
    """Generate a 128 BPM techno track: 4/4 kick, offbeat hihat, bass, pad."""
    bpm = 128
    samples = int(sr * duration_sec)
    output = np.zeros(samples)

    beat_dur = 60.0 / bpm
    beat_samples = int(beat_dur * sr)

    kick = _make_kick(sr)
    hihat = _make_hihat(sr)
    bass = _make_bass_note(sr, 55, 0.2)  # A1 = 55 Hz (A minor)
    pad = _make_pad(sr, 220, beat_dur * 4)  # A3

    num_beats = int(duration_sec / beat_dur)
    for i in range(num_beats):
        pos = int(i * beat_samples)
        # Kick on every beat
        end = min(pos + len(kick), samples)
        output[pos:end] += kick[:end - pos]
        # Hihat on offbeat
        offbeat = pos + beat_samples // 2
        end = min(offbeat + len(hihat), samples)
        if offbeat < samples:
            output[offbeat:end] += hihat[:end - offbeat]
        # Bass on every beat
        end = min(pos + len(bass), samples)
        output[pos:end] += bass[:end - pos]
        # Pad every 4 beats
        if i % 4 == 0:
            end = min(pos + len(pad), samples)
            output[pos:end] += pad[:end - pos]

    # Build energy: quiet intro, loud middle, breakdown, drop
    envelope = np.ones(samples)
    intro_end = samples // 6
    drop_start = samples // 2
    breakdown_start = samples * 2 // 5
    envelope[:intro_end] = np.linspace(0.3, 1.0, intro_end)
    envelope[breakdown_start:drop_start] = np.linspace(1.0, 0.3, drop_start - breakdown_start)
    output *= envelope

    # Normalize
    output = output / (np.max(np.abs(output)) + 1e-10) * 0.9

    import soundfile as sf
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, output, sr)


def generate_reggaeton_example(output_path: str, sr: int = 22050, duration_sec: float = 30.0):
    """Generate a 95 BPM reggaeton track: dembow pattern, bass."""
    bpm = 95
    samples = int(sr * duration_sec)
    output = np.zeros(samples)

    beat_dur = 60.0 / bpm
    beat_samples = int(beat_dur * sr)

    kick = _make_kick(sr, 0.12)
    hihat = _make_hihat(sr, 0.04)
    bass = _make_bass_note(sr, 73.42, 0.15)  # D2 (D minor)

    num_beats = int(duration_sec / beat_dur)
    for i in range(num_beats):
        pos = int(i * beat_samples)
        # Dembow pattern: kick on 1 and 3, snare-like on 2 and 4
        if i % 4 in [0, 2]:
            end = min(pos + len(kick), samples)
            output[pos:end] += kick[:end - pos]
        # Hihat on every 8th note
        for sub in range(2):
            sub_pos = pos + sub * (beat_samples // 2)
            end = min(sub_pos + len(hihat), samples)
            if sub_pos < samples:
                output[sub_pos:end] += hihat[:end - sub_pos]
        # Bass
        end = min(pos + len(bass), samples)
        output[pos:end] += bass[:end - pos]

    output = output / (np.max(np.abs(output)) + 1e-10) * 0.9

    import soundfile as sf
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, output, sr)


def generate_house_example(output_path: str, sr: int = 22050, duration_sec: float = 30.0):
    """Generate a 124 BPM house track: 4/4 kick, chord stabs."""
    bpm = 124
    samples = int(sr * duration_sec)
    output = np.zeros(samples)

    beat_dur = 60.0 / bpm
    beat_samples = int(beat_dur * sr)

    kick = _make_kick(sr, 0.13)
    hihat = _make_hihat(sr, 0.06)
    # C minor chord stab
    stab = _make_pad(sr, 261.63, 0.15) + _make_pad(sr, 311.13, 0.15) + _make_pad(sr, 392.0, 0.15)

    num_beats = int(duration_sec / beat_dur)
    for i in range(num_beats):
        pos = int(i * beat_samples)
        # Kick on every beat
        end = min(pos + len(kick), samples)
        output[pos:end] += kick[:end - pos]
        # Hihat offbeat
        offbeat = pos + beat_samples // 2
        end = min(offbeat + len(hihat), samples)
        if offbeat < samples:
            output[offbeat:end] += hihat[:end - offbeat]
        # Chord stab every 2 beats on the offbeat
        if i % 2 == 1:
            stab_pos = pos + beat_samples // 4
            end = min(stab_pos + len(stab), samples)
            if stab_pos < samples:
                output[stab_pos:end] += stab[:end - stab_pos]

    output = output / (np.max(np.abs(output)) + 1e-10) * 0.9

    import soundfile as sf
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, output, sr)


def generate_all_examples(output_dir: str):
    """Generate all example audio files."""
    generate_techno_example(os.path.join(output_dir, "techno_example.wav"))
    generate_reggaeton_example(os.path.join(output_dir, "reggaeton_example.wav"))
    generate_house_example(os.path.join(output_dir, "house_example.wav"))
    return [
        os.path.join(output_dir, "techno_example.wav"),
        os.path.join(output_dir, "reggaeton_example.wav"),
        os.path.join(output_dir, "house_example.wav"),
    ]
