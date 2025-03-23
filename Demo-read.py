# -------------------------------------------------------------
# Fichier : demo_read.py
# Auteur  : Paul Miailhe
# Date    : 21/03/2025
# Objet   : Prise de mesure
# -------------------------------------------------------------

import csv
import threading
import time
from datetime import datetime
from yr3180 import YR3180

class WeightLogger:
    def __init__(self, port='COM7', filename='log.csv', flush_interval=1.0):
        self.balance = YR3180(port=port, baudrate=115200)
        self.interval = 0.01  
        self.flush_interval = flush_interval
        self.filename = filename
        self.running = False
        self.thread = None
        self.buffer = []

        try:
            self.balance.set_filter(1)
            self.balance.set_speed(5)
            print("⚡ Configuration optimisée appliquée.")
        except Exception as e:
            print(f"⚠️ Erreur configuration vitesse : {e}")

    def _log_loop(self):
        last_flush = time.time()
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Poids (kg)'])

            while self.running:
                try:
                    weight = self.balance.read_weight_kg()
                    timestamp = datetime.now().isoformat(timespec='milliseconds')
                    self.buffer.append([timestamp, f"{weight:.3f}"])
                except Exception as e:
                    print(f"Erreur lecture : {e}")
                    break

                now = time.time()
                if now - last_flush >= self.flush_interval:
                    writer.writerows(self.buffer)
                    file.flush()
                    self.buffer.clear()
                    last_flush = now

                time.sleep(self.interval)

        self.balance.close()
        print("✅ Fin du logging. Port fermé.")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._log_loop, daemon=True)
        self.thread.start()
        print("🟢 Logger démarré.")

    def stop(self):
        self.running = False
        self.thread.join()
        print("🛑 Logger arrêté.")

if __name__ == '__main__':
    logger = WeightLogger(port='COM7', filename='log.csv')
    try:
        logger.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.stop()
