"""
DJ Copilot AI — EQ Advisor
Detects frequency collisions between two tracks and generates EQ suggestions.
"""
from database.models import EQAlert, EQAdvice, AlertLevel


def analyze_eq_collision(track_a: dict, track_b: dict) -> EQAdvice:
    """
    Analyze potential EQ collisions between Track A (playing) and Track B (incoming).
    Returns colored alerts with specific actions.
    """
    alerts = []

    bass_a = track_a.get("bass_intensity", 0)
    bass_b = track_b.get("bass_intensity", 0)
    mid_a = track_a.get("mid_intensity", 0)
    mid_b = track_b.get("mid_intensity", 0)
    high_a = track_a.get("high_intensity", 0)
    high_b = track_b.get("high_intensity", 0)
    vocal_a = track_a.get("vocal_presence", 0)
    vocal_b = track_b.get("vocal_presence", 0)

    # ── BASS Collision ──
    if bass_a > 0.4 and bass_b > 0.4:
        severity = (bass_a + bass_b) / 2
        if severity > 0.45:
            alerts.append(EQAlert(
                level=AlertLevel.DANGER,
                frequency_band="LOW",
                message=f"🔴 COLISIÓN DE GRAVES — Ambos tracks tienen graves pesados ({bass_a:.0%} vs {bass_b:.0%})",
                action="Corta LOWS del Deck B al mínimo antes de subir fader. Haz Bass Swap gradual.",
                value=0.0,
            ))
        else:
            alerts.append(EQAlert(
                level=AlertLevel.WARNING,
                frequency_band="LOW",
                message=f"🟡 Graves moderados en ambos decks ({bass_a:.0%} vs {bass_b:.0%})",
                action="Reduce LOWS del Deck B al 50% durante la transición",
                value=0.5,
            ))
    else:
        alerts.append(EQAlert(
            level=AlertLevel.SAFE,
            frequency_band="LOW",
            message="🟢 Graves compatibles — no hay colisión",
            action="LOWS libres, puedes mezclar sin cortar graves",
            value=1.0,
        ))

    # ── MID Collision (Vocals) ──
    if vocal_a > 0.4 and vocal_b > 0.4:
        alerts.append(EQAlert(
            level=AlertLevel.DANGER,
            frequency_band="MID",
            message=f"🔴 CONFLICTO VOCAL — Ambos tracks tienen presencia vocal alta ({vocal_a:.0%} vs {vocal_b:.0%})",
            action="Baja MIDS del Deck A al 30%. No mezcles durante hooks vocales.",
            value=0.3,
        ))
    elif mid_a > 0.45 and mid_b > 0.45:
        alerts.append(EQAlert(
            level=AlertLevel.WARNING,
            frequency_band="MID",
            message=f"🟡 Medios densos en ambos decks ({mid_a:.0%} vs {mid_b:.0%})",
            action="Reduce MIDS del Deck A gradualmente durante la transición",
            value=0.6,
        ))
    else:
        alerts.append(EQAlert(
            level=AlertLevel.SAFE,
            frequency_band="MID",
            message="🟢 Medios compatibles",
            action="MIDS libres",
            value=1.0,
        ))

    # ── HIGH Collision ──
    if high_a > 0.4 and high_b > 0.4:
        alerts.append(EQAlert(
            level=AlertLevel.WARNING,
            frequency_band="HIGH",
            message=f"🟡 Agudos intensos en ambos decks ({high_a:.0%} vs {high_b:.0%})",
            action="Reduce HIGHS del Deck A ligeramente para evitar fatiga auditiva",
            value=0.7,
        ))
    else:
        alerts.append(EQAlert(
            level=AlertLevel.SAFE,
            frequency_band="HIGH",
            message="🟢 Agudos compatibles",
            action="HIGHS libres",
            value=1.0,
        ))

    # Overall compatibility (average of band scores)
    danger_count = sum(1 for a in alerts if a.level == AlertLevel.DANGER)
    warning_count = sum(1 for a in alerts if a.level == AlertLevel.WARNING)
    overall = 1.0 - (danger_count * 0.3 + warning_count * 0.15)

    return EQAdvice(
        deck_a_track=track_a.get("title", "Unknown"),
        deck_b_track=track_b.get("title", "Unknown"),
        alerts=alerts,
        overall_compatibility=round(max(0, overall), 2),
    )
