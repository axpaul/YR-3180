# -------------------------------------------------------------
# Fichier : reset_yr3180_factory_like.py
# Auteur  : Paul Miailhe
# Date    : 22/03/2025
# Objet   : Remise à zéro complète des paramètres du module YR-3180
# -------------------------------------------------------------

"""
from yr3180 import YR3180
import time

def set_full_scale_factor(balance, factor):
    
    #Écrit manuellement le facteur d’échelle dans les registres 13–14.
    
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

"""

import time
from yr3180 import YR3180  # Assure-toi que ce fichier est bien dans le même dossier

def restore_yr3180_parameters(port='COM7'):
    balance = YR3180(port=port)
    print("Connexion établie.")

    try:
        print("Application des paramètres standards...")

        # dot: Nombre de décimales affichées
        balance.set_decimal_point(0)

        # Lb: graduation (increment)
        balance.set_graduation(20)

        # ad-H: vitesse d’acquisition
        balance.set_speed(1)

        # Clr: clear automatique (en secondes, ici 0.0005s = 0)
        balance._write_register(10, 0)  # Registre 10 = Auto clear delay

        # Fd: filtre
        balance.set_filter(1)

        # Zero: tare de démarrage ? (registre 11-12, valeur brute 1000)
        balance._write_register(11, 0)
        balance._write_register(12, 1000)

        # 2-t: pas un paramètre direct, mais sans doute temps clear ou calibration -> ignoré ici

        # Fset: full scale factor (registres 13-14)
        balance.set_full_scale_factor(1)

        print("Tous les paramètres ont été appliqués.")

    except Exception as e:
        print(f"Erreur pendant la configuration : {e}")

    finally:
        balance.close()
        print("Connexion fermée.")

if __name__ == "__main__":
    restore_yr3180_parameters()
