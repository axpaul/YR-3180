# -------------------------------------------------------------
# Fichier : test_all_commands.py
# Auteur  : Paul Miailhe
# Date    : 22/03/2025
# Objet   : Script de test global de toutes les commandes YR-3180
# -------------------------------------------------------------

from yr3180 import YR3180  # Assure-toi que ta classe est bien dans un fichier nommé yr3180.py

def test_all_get_commands():
    balance = YR3180(port='COM7')  # Modifie le port si besoin

    try:
        print("=== Lecture des valeurs de la balance YR-3180 ===")

        # Poids
        print("Poids brut (raw) :", balance.read_weight_raw())
        print("Poids en kg      :", balance.read_weight_kg())
        print("Poids (float)    :", balance.read_weight_float())

        # Paramètres système
        print("Décimales :", balance.get_decimal_point())
        print("Filtre    :", balance.get_filter())
        print("Vitesse   :", balance.get_speed())
        print("Graduation:", balance.get_graduation())
        print("Clear au démarrage :", balance.get_power_on_clear())

        # Communication
        print("Adresse Modbus :", balance.get_slave_address())
        print("Baudrate code  :", balance.get_baudrate_code())
        print("Checksum mode  :", balance.get_checksum_mode())

        # Alarmes
        print("Mode alarme :", balance.get_alarm_mode())
        print("AL1 - Seuil déclenchement :", balance.get_alarm_value(1))
        print("AL1 - Seuil retour        :", balance.get_alarm_return(1))
        print("AL1 - Statut              :", balance.get_alarm_status(1))
        print("AL2 - Seuil déclenchement :", balance.get_alarm_value(2))
        print("AL2 - Seuil retour        :", balance.get_alarm_return(2))
        print("AL2 - Statut              :", balance.get_alarm_status(2))

        # Calibration
        print("Facteur d’échelle (full scale):", balance.get_full_scale_factor())
        print("Calibration bas  (ADC) :", balance.get_calibration_low())
        print("Calibration haut (ADC) :", balance.get_calibration_high())

        # Diagnostiques
        print("Code ADC brut (original):", balance.get_original_code())
        print("Filtrage acquisition     :", balance.get_filter_code())
        print("Limite plage basse       :", balance.get_range_lower_limit())
        print("Limite plage haute       :", balance.get_range_upper_limit())

        # Infos complémentaires
        print("Temps d'effacement auto :", balance.get_automatic_clear_time())
        print("Valeur de tare actuelle :", balance.get_tare_value())
        print("Code format float       :", balance.get_float_format_code())

    except Exception as e:
        print("Erreur lors du test :", e)

    finally:
        balance.close()

if __name__ == "__main__":
    test_all_get_commands()

