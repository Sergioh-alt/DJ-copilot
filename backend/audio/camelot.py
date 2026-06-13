"""
DJ Copilot AI — Camelot Wheel Algorithm
Complete implementation of harmonic mixing logic with energy boost routing.
"""

# ── Camelot Wheel Mapping ──
# Maps musical keys to Camelot codes
KEY_TO_CAMELOT = {
    "C major": "8B", "A minor": "8A", "C": "8B", "Am": "8A",
    "G major": "9B", "E minor": "9A", "G": "9B", "Em": "9A",
    "D major": "10B", "B minor": "10A", "D": "10B", "Bm": "10A",
    "A major": "11B", "F# minor": "11A", "A": "11B", "F#m": "11A", "Gbm": "11A",
    "E major": "12B", "C# minor": "12A", "E": "12B", "C#m": "12A", "Dbm": "12A",
    "B major": "1B", "G# minor": "1A", "B": "1B", "G#m": "1A", "Abm": "1A",
    "F# major": "2B", "D# minor": "2A", "Gb": "2B", "D#m": "2A", "Ebm": "2A",
    "Db major": "3B", "Bb minor": "3A", "Db": "3B", "C#": "3B", "Bbm": "3A", "A#m": "3A",
    "Ab major": "4B", "F minor": "4A", "Ab": "4B", "G#": "4B", "Fm": "4A",
    "Eb major": "5B", "C minor": "5A", "Eb": "5B", "D#": "5B", "Cm": "5A",
    "Bb major": "6B", "G minor": "6A", "Bb": "6B", "A#": "6B", "Gm": "6A",
    "F major": "7B", "D minor": "7A", "F": "7B", "Dm": "7A",
}

CAMELOT_TO_KEY = {v: k for k, v in KEY_TO_CAMELOT.items()
                  if "#" not in k or "b" not in k}


def format_musical_key(key: str) -> str:
    """Format musical key to shorthand (e.g. 'D major' -> 'D', 'F minor' -> 'Fm')."""
    if not key or key == "Unknown":
        return "Unknown"
    
    # Remove "major" / "minor" and replace with shorthand
    clean = key.replace(" major", "").replace(" minor", "m")
    
    # Force Rekordbox flavor: If it's a Major key, convert to relative minor
    # (D -> Bm, C -> Am, etc.)
    rel_minor = {
        "C": "Am", "Db": "Bbm", "D": "Bm", "Eb": "Cm", "E": "Dbm", "F": "Dm",
        "Gb": "Ebm", "G": "Em", "Ab": "Fm", "A": "Gbm", "Bb": "Gm", "B": "Abm",
        "C#": "Bbm", "D#": "Cm", "F#": "Ebm", "G#": "Fm"
    }
    
    if clean in rel_minor:
        return rel_minor[clean]
        
    return clean


def key_to_camelot(key: str) -> str:
    """Convert a musical key string to its Camelot code."""
    if not key or key == "Unknown":
        return "1A"
    
    # Standard cleanup
    key = key.strip()
    
    # If the user wants Rekordbox style, we should probably just return the A code
    # for any relative major we find.
    # We'll use our dictionary but favor the 'A' (minor) codes.
    
    # Direct lookup
    if key in KEY_TO_CAMELOT:
        code = KEY_TO_CAMELOT[key]
        if code.endswith("B"):
            # Convert to A (Relative Minor)
            return code.replace("B", "A")
        return code
        
    # Handle "Bm", "Am", "C#m" formats
    key_alt = key.replace("minor", "m").replace("major", "").strip()
    if key_alt in KEY_TO_CAMELOT:
        code = KEY_TO_CAMELOT[key_alt]
        if code.endswith("B"):
            return code.replace("B", "A")
        return code
    
    # Try case-insensitive lookup
    for k, v in KEY_TO_CAMELOT.items():
        if k.lower() == key.lower() or k.lower().startswith(key.lower()):
            if v.endswith("B"):
                return v.replace("B", "A")
            return v

    return "1A"



def _parse_camelot(code: str) -> tuple:
    """Parse '8A' into (8, 'A')."""
    letter = code[-1].upper()
    number = int(code[:-1])
    return number, letter


def get_compatible_keys(camelot_code: str) -> dict:
    """
    Returns all compatible keys organized by match quality.
    """
    num, letter = _parse_camelot(camelot_code)
    opposite = "B" if letter == "A" else "A"

    result = {
        "perfect": [camelot_code],                                      # Same key
        "adjacent": [
            f"{((num - 2) % 12) + 1}{letter}",                         # -1
            f"{(num % 12) + 1}{letter}",                                # +1
        ],
        "modal": [f"{num}{opposite}"],                                  # A↔B
        "energy_boost": [f"{((num + 5) % 12) + 1}{letter}"],           # +7 positions
    }
    return result


def calculate_harmonic_score(code_a: str, code_b: str) -> tuple:
    """
    Calculate harmonic compatibility score between two Camelot codes.
    Returns (score: float 0-1, match_type: str).
    """
    if not code_a or not code_b:
        return 0.0, "unknown"

    num_a, let_a = _parse_camelot(code_a)
    num_b, let_b = _parse_camelot(code_b)

    # Perfect match
    if code_a == code_b:
        return 1.0, "perfect"

    # Adjacent (±1, same letter)
    diff = abs(num_a - num_b)
    circular_diff = min(diff, 12 - diff)
    if let_a == let_b and circular_diff == 1:
        return 0.9, "compatible"

    # Modal change (same number, different letter)
    if num_a == num_b and let_a != let_b:
        return 0.85, "compatible"

    # Energy boost (+7 circular positions, same letter)
    if let_a == let_b and circular_diff == 7:
        return 0.75, "energy_boost"

    # 2 steps away
    if let_a == let_b and circular_diff == 2:
        return 0.5, "risky"

    # Everything else
    return 0.1, "clash"


def get_all_camelot_codes() -> list:
    """Return all 24 Camelot codes."""
    codes = []
    for n in range(1, 13):
        codes.append(f"{n}A")
        codes.append(f"{n}B")
    return codes
