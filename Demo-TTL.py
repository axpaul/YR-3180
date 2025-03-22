import serial   # Pour gérer la communication série
import time     # (optionnel ici, utile si tu veux temporiser)

# Fonction pour calculer le CRC Modbus RTU
def calculate_crc(data):
    crc = 0xFFFF  # Valeur initiale du CRC
    for pos in data:
        crc ^= pos  # XOR avec l'octet courant
        for _ in range(8):  # 8 bits par octet
            lsb = crc & 0x0001  # Vérifie si le bit de poids faible est à 1
            crc >>= 1  # Décale d'un bit
            if lsb:
                crc ^= 0xA001  # Applique le polynôme Modbus si LSB = 1
    return crc.to_bytes(2, byteorder='little')  # CRC sur 2 octets, en little endian

# Création de la trame de requête :
# 0x01 : ID de l'esclave (adresse Modbus)
# 0x03 : Code fonction (lecture de registre holding)
# 0x00 0x00 : Adresse du registre de départ (0)
# 0x00 0x02 : Nombre de registres à lire (2)
request = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x02])
request += calculate_crc(request)  # Ajout du CRC calculé à la fin de la trame

# Ouverture de la communication série avec les bons paramètres
with serial.Serial('COM7', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1) as ser:
    ser.write(request)  # Envoi de la trame Modbus sur le port série

    # Lecture de la réponse :
    # Attendu : 1 octet (adresse) + 1 (fonction) + 1 (nb d’octets) + 4 (données) + 2 (CRC) = 9
    response = ser.read(9)

    # Vérifie qu’on a bien reçu au moins les 4 octets de données
    if len(response) >= 7:
        raw = response[3:7]  # Extraction des 4 octets de données (deux registres 16 bits)
        value = int.from_bytes(raw, byteorder='big')  # Fusionne les 4 octets en un entier 32 bits
        print(f"Poids brut : {value} / {value / 1000:.3f} kg")  # Affiche le poids avec conversion
    else:
        print("Réponse invalide :", response)  # Affiche la réponse brute si elle est trop courte
