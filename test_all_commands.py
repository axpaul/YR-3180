# -------------------------------------------------------------
# Fichier : test_all_commands.py
# Auteur  : Paul Miailhe
# Date    : 22/03/2025
# Objet   : Script de test pour lire tous les paramètres du module YR-3180
# -------------------------------------------------------------

import serial
import struct

from yr3180 import YR3180 

def test_all_get_commands():
    print("---- Test de lecture des registres YR-3180 ----")
    balance = YR3180(port='COM7')  # Change le port si besoin
    try:
        print("Poids brut :", balance.read_weight_raw())
        print("Poids en kg :", balance.read_weight_kg())
        print("Poids (float) :", balance.read_weight_float())

        print("Decimal Point :", balance.get_decimal_point())
        print("Filter :", balance.get_filter())
        print("Speed :", balance.get_speed())
        print("Graduation :", balance.get_graduation())
        print("Power On Clear :", balance.get_power_on_clear())

        print("Adresse Modbus :", balance.get_slave_address())
        print("Baudrate Code :", balance.get_baudrate_code())
        print("Checksum Mode :", balance.get_checksum_mode())
        print("Float Format Code :", balance.get_float_format_code())

        print("AL1 - Seuil déclenchement :", balance.get_alarm_value(1))
        print("AL1 - Seuil retour        :", balance.get_alarm_return(1))
        print("AL1 - Statut              :", balance.get_alarm_status(1))

        print("AL2 - Seuil déclenchement :", balance.get_alarm_value(2))
        print("AL2 - Seuil retour        :", balance.get_alarm_return(2))
        print("AL2 - Statut              :", balance.get_alarm_status(2))

        print("Mode d'alarme :", balance.get_alarm_mode())

        print("Full Scale Factor :", balance.get_full_scale_factor())
        print("Calibration LOW :", balance.get_calibration_low())
        print("Calibration HIGH :", balance.get_calibration_high())

        print("Filter Code :", balance.get_filter_code())
        print("Original Code (ADC) :", balance.get_original_code())
        print("Range Lower Limit :", balance.get_range_lower_limit())
        print("Range Upper Limit :", balance.get_range_upper_limit())

        print("Automatic Clear Time :", balance.get_automatic_clear_time())
        print("Tare Value :", balance.get_tare_value())

    except Exception as e:
        print("Erreur pendant le test :", e)
    finally:
        balance.close()
        print("Connexion fermée.")

if __name__ == "__main__":
    test_all_get_commands()
