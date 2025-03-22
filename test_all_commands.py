# -------------------------------------------------------------
# Fichier : test_all_commands.py
# Auteur  : Paul Miailhe
# Date    : 22/03/2025
# Objet   : Script de test global de toutes les commandes YR-3180
# -------------------------------------------------------------

from yr3180 import YR3180
import time

balance = YR3180(port='COM7')  # 🔧 adapter le port ici

try:
    print("===== TEST LECTURES =====")
    print(f"Poids brut        : {balance.read_weight_raw()} (int32)")
    print(f"Poids en kg       : {balance.read_weight_kg():.3f} kg")
    print(f"Poids flottant    : {balance.read_weight_float():.3f} kg")

    print(f"Décimales         : {balance.get_decimal_point()}")
    print(f"Filtrage          : {balance.get_filter()}")
    print(f"Vitesse d'acq.    : {balance.get_speed()}")
    print(f"Graduation        : {balance.get_graduation()}")
    print(f"Effacement au démarrage : {balance.get_power_on_clear()}")

    print(f"Adresse Modbus    : {balance.get_slave_address()}")
    print(f"Baudrate code     : {balance.get_baudrate_code()}")
    print(f"Checksum mode     : {balance.get_checksum_mode()}")

    print(f"Alarme 1 statut   : {balance.get_alarm_status(1)}")
    print(f"Alarme 1 valeur   : {balance.get_alarm_value(1)}")
    print(f"Alarme 1 retour   : {balance.get_alarm_return(1)}")

    print(f"Alarme 2 statut   : {balance.get_alarm_status(2)}")
    print(f"Alarme 2 valeur   : {balance.get_alarm_value(2)}")
    print(f"Alarme 2 retour   : {balance.get_alarm_return(2)}")

    print("\n===== TEST COMMANDES ACTIVES =====")
    print("→ Tare...")
    balance.tare()
    time.sleep(0.5)

    print("→ Calibration bas...")
    balance.calibrate_lower()
    time.sleep(0.5)

    print("→ Calibration haut...")
    balance.calibrate_upper()
    time.sleep(0.5)

    print("→ Annulation tare...")
    balance.cancel_tare()
    time.sleep(0.5)

    print("→ Effacement automatique...")
    balance.auto_clear()
    time.sleep(0.5)

    print("\n✅ Tous les tests ont été envoyés.")

except Exception as e:
    print("❌ Erreur pendant les tests :", e)

finally:
    balance.close()
