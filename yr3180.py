import serial   # Pour communiquer en port série
import struct   # Pour décoder les valeurs binaires (float notamment)

class YR3180:
    def __init__(self, port='COM7', baudrate=9600, slave_address=0x01):
        """
        Initialise la connexion série avec les paramètres standard de la YR-3180
        """
        self.port = port
        self.baudrate = baudrate
        self.slave_address = slave_address
        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )

    def close(self):
        """
        Ferme proprement le port série
        """
        self.serial.close()

    def _calculate_crc(self, data):
        """
        Calcule le CRC Modbus RTU à partir de la trame (hors CRC)
        → Utilise le polynôme 0xA001 (standard Modbus)
        → Retourne le CRC sur 2 octets (little endian)
        """
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                lsb = crc & 0x0001
                crc >>= 1
                if lsb:
                    crc ^= 0xA001
        return crc.to_bytes(2, byteorder='little')  # CRC = little endian (LSB first)

    def _build_request(self, function, register, value=None, count=1):
        """
        Construit une trame Modbus RTU à envoyer :
        - Pour lecture : fonction 0x03, count = nombre de registres à lire
        - Pour écriture : fonction 0x06, value = valeur 16 bits à écrire
        Structure : [adresse][fonction][reg_H][reg_L][val_H][val_L][CRC_L][CRC_H]
        """
        request = bytearray([
            self.slave_address,         # Adresse de l'esclave
            function,                   # Code fonction Modbus
            (register >> 8) & 0xFF,     # MSB de l'adresse du registre
            register & 0xFF             # LSB du registre
        ])

        if function == 0x03:
            request += count.to_bytes(2, byteorder='big')  # Nombre de registres à lire
        elif function == 0x06:
            request += value.to_bytes(2, byteorder='big')  # Valeur 16 bits à écrire
        else:
            raise NotImplementedError("Fonction Modbus non supportée ici")

        request += self._calculate_crc(request)  # Ajout du CRC (2 octets LSB/MSB)
        return request

    def _send_request(self, request, expected_response_length):
        """
        Envoie la requête sur le port série et lit la réponse attendue
        """
        self.serial.write(request)
        return self.serial.read(expected_response_length)

    def _read_registers(self, register, count):
        """
        Lecture de `count` registres Modbus à partir de l'adresse `register`
        - Retourne les octets de données (sans en-tête ni CRC)
        """
        request = self._build_request(0x03, register, count=count)
        response = self._send_request(request, 5 + 2 * count)  # 5 = header + CRC
        if len(response) >= 5 + 2 * count:
            return response[3:3 + 2 * count]  # Extraction des octets de données
        else:
            raise ValueError(f"Réponse invalide : {response.hex()}")

    def _write_register(self, register, value):
        """
        Écriture d'un registre unique via la fonction 0x06
        """
        request = self._build_request(0x06, register, value=value)
        response = self._send_request(request, 8)  # Réponse = écho exact
        if response != request:
            raise ValueError(f"Écriture échouée. Réponse : {response.hex()}")

    # ---------------------- Lecture des données ----------------------

    def read_weight_raw(self):
        """
        Lit le poids brut (registres 0 et 1) sous forme de entier signé 32 bits
        """
        data = self._read_registers(0, 2)
        return int.from_bytes(data, byteorder='big', signed=True)

    def read_weight_kg(self):
        """
        Retourne le poids converti en kilogrammes (avec 3 décimales)
        """
        return self.read_weight_raw() / 1000.0

    def read_weight_float(self):
        """
        Lit le poids au format float 32 bits (registre 2 et 3)
        """
        data = self._read_registers(2, 2)
        return struct.unpack('>f', data)[0]  # '>f' = float big endian

    # ---------------------- Commandes directes ----------------------

    def tare(self):
        """Effectue une tare (mise à zéro du poids actuel)"""
        self._write_register(33, 1)

    def cancel_tare(self):
        """Annule la tare appliquée précédemment"""
        self._write_register(33, 2)

    def calibrate_lower(self):
        """Déclenche la calibration du point bas (poids = 0)"""
        self._write_register(32, 1)

    def calibrate_upper(self):
        """Déclenche la calibration du point haut (poids = poids max)"""
        self._write_register(32, 2)

    def auto_clear(self):
        """Déclenche un effacement automatique si la config le permet"""
        self._write_register(9, 1)

    # ---------------------- Paramètres système ----------------------

    def get_decimal_point(self):
        """Lit le nombre de décimales affichées (registre 4)"""
        return int.from_bytes(self._read_registers(4, 1), byteorder='big')

    def set_decimal_point(self, value):
        """Change le nombre de décimales (registre 4)"""
        self._write_register(4, value)

    def get_filter(self):
        """Lit la valeur de filtre appliquée (registre 5)"""
        return int.from_bytes(self._read_registers(5, 1), byteorder='big')

    def set_filter(self, value):
        """Définit le niveau de filtrage (registre 5)"""
        self._write_register(5, value)

    def get_speed(self):
        """Lit la vitesse d'acquisition (registre 6)"""
        return int.from_bytes(self._read_registers(6, 1), byteorder='big')

    def set_speed(self, value):
        """Change la vitesse d'acquisition (registre 6)"""
        self._write_register(6, value)

    def get_graduation(self):
        """Lit la graduation de la balance (registre 7)"""
        return int.from_bytes(self._read_registers(7, 1), byteorder='big')

    def set_graduation(self, value):
        """Change la valeur de graduation (registre 7)"""
        self._write_register(7, value)

    def get_power_on_clear(self):
        """Retourne le mode d’effacement au démarrage (registre 8)"""
        return int.from_bytes(self._read_registers(8, 1), byteorder='big')

    def set_power_on_clear(self, value):
        """Modifie le mode d’effacement au démarrage (registre 8)"""
        self._write_register(8, value)

    def get_slave_address(self):
        """Lit l'adresse Modbus de la balance (registre 27)"""
        return int.from_bytes(self._read_registers(27, 1), byteorder='big')

    def get_baudrate_code(self):
        """Lit le code du baudrate configuré (registre 28)"""
        return int.from_bytes(self._read_registers(28, 1), byteorder='big')

    def get_checksum_mode(self):
        """Lit le mode de vérification (registre 29)"""
        return int.from_bytes(self._read_registers(29, 1), byteorder='big')

    # ---------------------- Alarmes ----------------------

    def get_alarm_value(self, alarm=1):
        """
        Lit la valeur de déclenchement de l'alarme :
        AL1 → registres 53-54
        AL2 → registres 56-57
        """
        address = 53 if alarm == 1 else 56
        data = self._read_registers(address, 2)
        return int.from_bytes(data, byteorder='big', signed=True)

    def get_alarm_return(self, alarm=1):
        """
        Lit la valeur de retour (seuil de réarmement) :
        AL1 → registres 58-59
        AL2 → registres 60-61
        """
        address = 58 if alarm == 1 else 60
        data = self._read_registers(address, 2)
        return int.from_bytes(data, byteorder='big', signed=True)

    def get_alarm_status(self, alarm=1):
        """
        Lit le statut d’activation actuel de l'alarme (ON/OFF) :
        AL1 → registre 80
        AL2 → registre 81
        """
        address = 80 if alarm == 1 else 81
        return int.from_bytes(self._read_registers(address, 1), byteorder='big')
