"""
DJ Copilot AI — Custom Sample Generator
Generates mock songs for testing.
"""
import os
import numpy as np
import soundfile as sf
from audio.synth_examples import _make_kick, _make_hihat, _make_bass_note, _make_pad

def generate_trance_track(output_path, title, bpm=138, duration=60):
    sr = 22050
    samples = int(sr * duration)
    output = np.zeros(samples)
    beat_dur = 60.0 / bpm
    beat_samples = int(beat_dur * sr)

    kick = _make_kick(sr, 0.15)
    hihat = _make_hihat(sr, 0.08)
    bass = _make_bass_note(sr, 65.41, 0.2) # C2
    lead = _make_pad(sr, 523.25, beat_dur * 2) # C5

    num_beats = int(duration / beat_dur)
    for i in range(num_beats):
        pos = int(i * beat_samples)
        # Kick on every beat
        end = min(pos + len(kick), samples)
        output[pos:end] += kick[:end - pos]
        # Hihat on every offbeat
        offbeat = pos + beat_samples // 2
        if offbeat < samples:
            end = min(offbeat + len(hihat), samples)
            output[offbeat:end] += hihat[:end - offbeat]
        # Fast rolling bass
        for sub in range(4):
            sub_pos = pos + sub * (beat_samples // 4)
            if sub_pos < samples:
                end = min(sub_pos + len(bass), samples)
                output[sub_pos:end] += bass[:end - sub_pos]
        # Trance Lead every 16 beats
        if i % 16 == 0:
            end = min(pos + len(lead), samples)
            output[pos:end] += lead[:end - pos]

    output = output / (np.max(np.abs(output)) + 1e-10) * 0.8
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, output, sr)
    print(f"Generated: {output_path}")

def generate_house_track(output_path, title, bpm=124, duration=60):
    sr = 22050
    samples = int(sr * duration)
    output = np.zeros(samples)
    beat_dur = 60.0 / bpm
    beat_samples = int(beat_dur * sr)

    kick = _make_kick(sr, 0.13)
    hihat = _make_hihat(sr, 0.06)
    chord = _make_pad(sr, 329.63, 0.2) # E4

    num_beats = int(duration / beat_dur)
    for i in range(num_beats):
        pos = int(i * beat_samples)
        end = min(pos + len(kick), samples)
        output[pos:end] += kick[:end - pos]
        offbeat = pos + beat_samples // 2
        if offbeat < samples:
            end = min(offbeat + len(hihat), samples)
            output[offbeat:end] += hihat[:end - offbeat]
        if i % 4 == 2: # Funkier placement
            stab_pos = pos + beat_samples // 4
            if stab_pos < samples:
                end = min(stab_pos + len(chord), samples)
                output[stab_pos:end] += chord[:end - stab_pos]

    output = output / (np.max(np.abs(output)) + 1e-10) * 0.8
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, output, sr)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    data_dir = os.path.join(os.getcwd(), "data", "test_tracks")
    generate_trance_track(os.path.join(data_dir, "Paul_van_Dyk_For_An_Angel_Mock.wav"), "For An Angel")
    generate_trance_track(os.path.join(data_dir, "Paul_van_Dyk_Nothing_But_You_Mock.wav"), "Nothing But You")
    generate_house_track(os.path.join(data_dir, "Daft_Punk_One_More_Time_Mock.wav"), "One More Time")
