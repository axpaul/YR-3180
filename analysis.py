# -------------------------------------------------------------
# Fichier : analysis.py
# Objet   : Fonctions pures d'analyse d'un tir (banc de poussée)
#           Pas de dépendance Qt -> testable en isolation.
# -------------------------------------------------------------

from __future__ import annotations

import numpy as np

G0 = 9.80665  # accélération standard (m/s²) pour la conversion kg -> N et l'Isp


def kg_to_newton(mass_kg):
    return np.asarray(mass_kg, dtype=float) * G0


def peak_thrust(t, force):
    """Retourne (t_peak, F_peak). Renvoie (None, 0.0) si tableau vide."""
    t = np.asarray(t)
    f = np.asarray(force)
    if t.size == 0:
        return None, 0.0
    i = int(np.argmax(f))
    return float(t[i]), float(f[i])


def burn_window(t, force, threshold_n=2.0, min_duration_s=0.05, release_s=0.5):
    """
    Détecte la fenêtre de combustion par hystérésis simple :
      - début : première fois que F > threshold pendant >= min_duration_s
      - fin   : F < threshold pendant >= release_s après le début

    Retourne (t_start, t_end) ou (None, None) si rien détecté.
    """
    t = np.asarray(t, dtype=float)
    f = np.asarray(force, dtype=float)
    if t.size < 2:
        return None, None

    above = f > threshold_n

    t_start = None
    run_start = None
    for i in range(t.size):
        if above[i]:
            if run_start is None:
                run_start = t[i]
            elif t[i] - run_start >= min_duration_s:
                t_start = run_start
                break
        else:
            run_start = None

    if t_start is None:
        return None, None

    # fin : on cherche release_s consécutives sous le seuil après t_start
    t_end = None
    below_start = None
    for i in range(t.size):
        if t[i] < t_start:
            continue
        if not above[i]:
            if below_start is None:
                below_start = t[i]
            elif t[i] - below_start >= release_s:
                t_end = below_start
                break
        else:
            below_start = None

    if t_end is None:
        t_end = float(t[-1])

    return float(t_start), float(t_end)


def total_impulse(t, force, t_start=None, t_end=None):
    """
    Impulsion totale (N·s) = intégrale trapézoïdale de F sur [t_start, t_end].
    Si les bornes sont None, intègre sur tout le tableau.
    """
    t = np.asarray(t, dtype=float)
    f = np.asarray(force, dtype=float)
    if t.size < 2:
        return 0.0

    if t_start is None:
        t_start = float(t[0])
    if t_end is None:
        t_end = float(t[-1])

    mask = (t >= t_start) & (t <= t_end)
    if mask.sum() < 2:
        return 0.0

    # np.trapezoid (numpy >= 2.0) ; fallback sur trapz pour les versions anciennes
    trap = getattr(np, "trapezoid", None) or np.trapz
    return float(trap(f[mask], t[mask]))


def average_thrust(t, force, t_start=None, t_end=None):
    """Poussée moyenne sur la fenêtre = impulsion / durée."""
    if t_start is None or t_end is None:
        t = np.asarray(t)
        if t.size == 0:
            return 0.0
        t_start, t_end = float(t[0]), float(t[-1])
    duration = max(t_end - t_start, 1e-9)
    return total_impulse(t, force, t_start, t_end) / duration


def specific_impulse(impulse_ns, propellant_mass_kg):
    """Isp = It / (m * g0). Retourne 0 si masse nulle."""
    if propellant_mass_kg <= 0:
        return 0.0
    return impulse_ns / (propellant_mass_kg * G0)


def summarize(t, force, threshold_n=2.0, propellant_mass_kg=0.0):
    """
    Calcule l'ensemble des indicateurs d'un tir et renvoie un dict prêt à
    afficher / sérialiser dans un rapport texte.
    """
    t_start, t_end = burn_window(t, force, threshold_n=threshold_n)
    t_peak, f_peak = peak_thrust(t, force)

    if t_start is not None and t_end is not None:
        duration = t_end - t_start
        impulse = total_impulse(t, force, t_start, t_end)
        avg = impulse / duration if duration > 0 else 0.0
    else:
        duration = 0.0
        impulse = 0.0
        avg = 0.0

    isp = specific_impulse(impulse, propellant_mass_kg)

    return {
        "t_start": t_start,
        "t_end": t_end,
        "duration_s": duration,
        "peak_n": f_peak,
        "t_peak": t_peak,
        "impulse_ns": impulse,
        "average_n": avg,
        "isp_s": isp,
    }


def format_report(summary, propellant_mass_kg=0.0):
    """Formate le résumé en texte lisible (rapport `.txt`)."""
    lines = [
        "=== Rapport de tir ===",
        f"Pic de poussée      : {summary['peak_n']:.2f} N",
        f"Instant du pic      : {summary['t_peak']:.3f} s" if summary['t_peak'] is not None else "Instant du pic      : -",
        f"Durée combustion    : {summary['duration_s']:.3f} s",
        f"Poussée moyenne     : {summary['average_n']:.2f} N",
        f"Impulsion totale    : {summary['impulse_ns']:.2f} N·s",
    ]
    if propellant_mass_kg > 0:
        lines.append(f"Masse propergol     : {propellant_mass_kg*1000:.1f} g")
        lines.append(f"Impulsion spécifique : {summary['isp_s']:.1f} s")
    return "\n".join(lines)
