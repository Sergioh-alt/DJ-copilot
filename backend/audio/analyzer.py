"""
DJ Copilot AI — Audio Analyzer
Uses librosa to extract musical features from audio files.
This is the core of the "Deep Listening" engine.
"""
import numpy as np
import librosa
import mutagen
from audio.camelot import key_to_camelot, format_musical_key
from database.models import TrackFeatures


# ── Key Detection via Chroma ──
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                           2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                           2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

KEY_NAMES_MAJOR = ["C major", "C# major", "D major", "Eb major",
                    "E major", "F major", "F# major", "G major",
                    "Ab major", "A major", "Bb major", "B major"]
KEY_NAMES_MINOR = ["C minor", "C# minor", "D minor", "Eb minor",
                    "E minor", "F minor", "F# minor", "G minor",
                    "Ab minor", "A minor", "Bb minor", "B minor"]


def detect_key(y: np.ndarray, sr: int) -> str:
    """Detect musical key using chroma correlation with Krumhansl profiles."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    major_corrs = []
    minor_corrs = []
    for shift in range(12):
        shifted_major = np.roll(MAJOR_PROFILE, shift)
        shifted_minor = np.roll(MINOR_PROFILE, shift)
        major_corrs.append(np.corrcoef(chroma_mean, shifted_major)[0, 1])
        minor_corrs.append(np.corrcoef(chroma_mean, shifted_minor)[0, 1])

    max_major = max(major_corrs)
    max_minor = max(minor_corrs)

    if max_major >= max_minor:
        return KEY_NAMES_MAJOR[major_corrs.index(max_major)]
    else:
        return KEY_NAMES_MINOR[minor_corrs.index(max_minor)]


def analyze_track(file_path: str) -> TrackFeatures:
    """
    Full analysis pipeline for a single audio file.
    Extracts: BPM, key, energy, bass/mid/high intensity, vocal presence,
    groove density, drops, breakdowns, phrase length.
    """
    # Load audio (mono, 22050Hz for speed)
    y, sr = librosa.load(file_path, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # ── Metadata Extraction (ID3/MP4/FLAC/WAV Tags) ──
    tag_bpm = 0.0
    tag_key = "Unknown"
    try:
        audio = mutagen.File(file_path)
        if audio:
            # Try to get BPM
            bpm_keys = ['TBPM', 'bpm', 'tmpo', 'tempo', 'fBPM', 'FBPM']
            for k in bpm_keys:
                if k in audio:
                    val = str(audio[k][0])
                    try:
                        tag_bpm = float(val.split()[0])
                        print(f"[Metadata] BPM encontrado en tag '{k}': {tag_bpm}")
                        break
                    except: continue
            
            # Try to get Key
            key_keys = ['TKEY', 'initialkey', 'key', 'TIT3', 'KEY']
            for k in key_keys:
                if k in audio:
                    tag_key = str(audio[k][0])
                    print(f"[Metadata] Key encontrada en tag '{k}': {tag_key}")
                    break
            
            # Check COMM for "key: Bm" or similar (some versions of Rekordbox/MixedInKey)
            if tag_key == "Unknown" and 'COMM' in audio:
                comm_text = str(audio['COMM'])
                if "key:" in comm_text.lower():
                    # Extract something like "key: Bm"
                    import re
                    match = re.search(r"key:\s*([A-Ga-g#b]+m?)", comm_text, re.I)
                    if match:
                        tag_key = match.group(1)
                        print(f"[Metadata] Key encontrada en COMM: {tag_key}")
    except Exception as e:
        print(f"[Metadata] Error leyendo tags: {e}")

    # ── BPM ──
    if tag_bpm > 0:
        bpm = tag_bpm
    else:
        print(f"[IA] Detectando BPM mediante audio...")
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(np.round(tempo, 1)) if np.isscalar(tempo) else float(np.round(tempo[0], 1))

    # ── Key ──
    if tag_key != "Unknown":
        key_name = tag_key
    else:
        print(f"[IA] Detectando Key mediante audio...")
        key_name = detect_key(y, sr)
        # Electronic music (Trance/Techno) is 90% minor keys. 
        # If IA detected a Major key, we check if it could be the relative minor.
        # This is a common "Rekordbox flavor" fix.
    
    camelot_code = key_to_camelot(key_name)
    
    # Final check: If user wants "Bm" and we have "D" (Relative major), 
    # and it's a Trance track (detected by energy/style), we could shift it.
    # But for now, let's just make sure we format what we have.
    key_name = format_musical_key(key_name)

    # ── Energy Curve (RMS per 4-bar segments) ──
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    # Segment into ~4-bar chunks (assuming 4/4 time)
    beats_per_bar = 4
    bars_per_segment = 4
    if bpm > 0:
        seconds_per_segment = (60.0 / bpm) * beats_per_bar * bars_per_segment
        frames_per_segment = int(seconds_per_segment * sr / hop_length)
    else:
        frames_per_segment = len(rms)

    energy_curve = []
    if frames_per_segment > 0:
        for i in range(0, len(rms), max(1, frames_per_segment)):
            segment = rms[i:i + frames_per_segment]
            if len(segment) > 0:
                energy_curve.append(float(np.mean(segment)))

    # Normalize energy curve
    max_e = max(energy_curve) if energy_curve else 1.0
    if max_e > 0:
        energy_curve = [round(e / max_e, 3) for e in energy_curve]

    overall_energy = float(np.mean(energy_curve)) if energy_curve else 0.0

    # ── Spectral Analysis (Bass / Mid / High) ──
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    # Bass: 20-250 Hz, Mid: 250-4000 Hz, High: 4000+ Hz
    bass_mask = (freqs >= 20) & (freqs < 250)
    mid_mask = (freqs >= 250) & (freqs < 4000)
    high_mask = freqs >= 4000

    total_energy_spec = np.mean(spec) + 1e-10
    bass_intensity = float(np.clip(np.mean(spec[bass_mask]) / total_energy_spec, 0, 1))
    mid_intensity = float(np.clip(np.mean(spec[mid_mask]) / total_energy_spec, 0, 1))
    high_intensity = float(np.clip(np.mean(spec[high_mask]) / total_energy_spec, 0, 1))

    # Normalize so they represent proportions
    total_band = bass_intensity + mid_intensity + high_intensity
    if total_band > 0:
        bass_intensity = round(bass_intensity / total_band, 3)
        mid_intensity = round(mid_intensity / total_band, 3)
        high_intensity = round(high_intensity / total_band, 3)

    # ── Vocal Presence Estimation ──
    # Vocal range: spectral flatness in 300Hz-4kHz band
    vocal_mask = (freqs >= 300) & (freqs < 4000)
    vocal_spec = spec[vocal_mask]
    spectral_flat = float(np.mean(librosa.feature.spectral_flatness(S=vocal_spec)))
    # Lower flatness in vocal range = more tonal/vocal content
    vocal_presence = round(float(np.clip(1.0 - spectral_flat * 3, 0, 1)), 3)

    # ── Groove Density (onset rate) ──
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = len(onsets) / max(duration, 1.0)
    # Normalize: typical range 1-8 onsets/sec for dance music
    groove_density = round(float(np.clip(onset_rate / 8.0, 0, 1)), 3)

    # ── Drop Detection (sudden energy increase) ──
    drop_positions = []
    breakdown_positions = []
    if len(energy_curve) > 2:
        for i in range(1, len(energy_curve)):
            diff = energy_curve[i] - energy_curve[i - 1]
            time_pos = round(i * (duration / len(energy_curve)), 2)
            if diff > 0.3:  # Sudden energy jump = drop
                drop_positions.append(time_pos)
            elif diff < -0.3:  # Sudden energy fall = breakdown
                breakdown_positions.append(time_pos)

    # ── Phrase Length Estimation ──
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    if len(beat_times) > 16:
        phrase_length = float(beats_per_bar * bars_per_segment)
    else:
        phrase_length = float(len(beat_times))

    # ── Spectral Centroid ──
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_mean = float(np.mean(centroid))

    return TrackFeatures(
        bpm=bpm,
        key=key_name,
        camelot_code=camelot_code,
        energy=round(overall_energy, 3),
        energy_curve=energy_curve,
        bass_intensity=bass_intensity,
        mid_intensity=mid_intensity,
        high_intensity=high_intensity,
        vocal_presence=vocal_presence,
        groove_density=groove_density,
        drop_positions=drop_positions,
        breakdown_positions=breakdown_positions,
        phrase_length=phrase_length,
        duration=round(duration, 2),
        spectral_centroid_mean=round(centroid_mean, 2),
        embedding=[]  # filled by feature_extractor
    )
