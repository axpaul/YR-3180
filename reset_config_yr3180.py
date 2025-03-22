# -------------------------------------------------------------
# Fichier : reset_yr3180_factory_like.py
# Auteur  : Paul Miailhe
# Date    : 22/03/2025
# Objet   : Remise à zéro complète des paramètres du module YR-3180
# -------------------------------------------------------------

from yr3180 import YR3180
import time

def set_full_scale_factor(balance, factor):
    """
    Écrit manuellement le facteur d’échelle dans les registres 13–14.
    """
    msb = (factor >> 16) & 0xFFFF
    lsb = factor & 0xFFFF
    balance._write_register(13, msb)
    balance._write_register(14, lsb)

balance = YR3180('COM7')  # Adapter le port

try:
    # 1. Calibration du point bas (sans charge)
    input("🔹 Étape 1 : Retire toute charge de la balance, puis appuie sur [Entrée]...")
    balance.calibrate_lower()
    print("✅ Calibration bas enregistrée.")
    time.sleep(1)

    # 2. Pose d'une masse connue
    masse_kg = float(input("⚖️ Indique la masse que tu vas poser (en kg) : "))
    input(f"👉 Pose maintenant {masse_kg:.3f} kg sur le capteur, puis appuie sur [Entrée]...")

    valeur_brute = balance.read_weight_raw()
    print(f"🔎 Valeur brute lue avec {masse_kg:.3f} kg : {valeur_brute}")

    # 3. Calcul du facteur pour 20 kg
    facteur = int(valeur_brute * (20.0 / masse_kg))
    print(f"🧮 Facteur d’échelle calculé pour 20.000 kg : {facteur}")

    # 4. Écriture dans les registres 13–14
    set_full_scale_factor(balance, facteur)
    print("✅ Facteur d’échelle écrit dans la balance.")

    # 5. Tare et vérification finale
    balance.cancel_tare()
    balance.tare()
    poids = balance.read_weight_kg()
    print(f"\n📏 Poids mesuré : {poids:.3f} kg")

    print("\n🎉 Calibration terminée. Balance configurée pour 0 → 20 kg.")

finally:
    balance.close()

