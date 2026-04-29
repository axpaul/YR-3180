# -------------------------------------------------------------
# Fichier : acquisition.py
# Objet   : Worker QThread d'acquisition continue du capteur YR-3180.
#           Émet un signal Qt à chaque échantillon ; les commandes
#           ponctuelles (tare, set_filter, set_speed) sont envoyées
#           via une file pour rester thread-safe.
# -------------------------------------------------------------

from __future__ import annotations

import csv
import queue
import time
from collections import deque

from PySide6.QtCore import QThread, Signal, Slot

from yr3180 import YR3180, CRCError, ModbusTimeoutError

G0 = 9.80665


class AcquisitionWorker(QThread):
    sample = Signal(float, float)              # t (s relatif au start), force (N)
    connection_lost = Signal(str)
    status = Signal(str)
    rate = Signal(float)                       # fréquence d'acquisition mesurée (Hz)

    def __init__(self, port, baudrate=9600, slave_address=0x01,
                 buffer_size=120_000, parent=None):
        super().__init__(parent)
        self._port = port
        self._baudrate = baudrate
        self._slave_address = slave_address
        self._device: YR3180 | None = None
        self._stop_requested = False
        self._command_queue: queue.Queue = queue.Queue()
        self._buffer: deque = deque(maxlen=buffer_size)
        self._t0: float | None = None

    # --- API publique appelée depuis le thread GUI ---

    def request_tare(self):
        self._command_queue.put(("tare", None))

    def request_cancel_tare(self):
        self._command_queue.put(("cancel_tare", None))

    def request_set_filter(self, value):
        self._command_queue.put(("set_filter", int(value)))

    def request_set_speed(self, value):
        self._command_queue.put(("set_speed", int(value)))

    def request_calibrate_lower(self):
        self._command_queue.put(("calibrate_lower", None))

    def request_calibrate_upper(self):
        self._command_queue.put(("calibrate_upper", None))

    def stop(self):
        self._stop_requested = True

    def snapshot(self):
        """Retourne une copie list[(t, F)] du buffer interne (thread-safe car
        deque est protégé par le GIL pour les opérations atomiques)."""
        return list(self._buffer)

    def clear_buffer(self):
        self._buffer.clear()
        self._t0 = None

    # --- boucle thread ---

    def run(self):
        try:
            self._device = YR3180(
                port=self._port,
                baudrate=self._baudrate,
                slave_address=self._slave_address,
                timeout=0.2,
                retries=3,
            )
        except Exception as exc:
            self.connection_lost.emit(f"Ouverture du port {self._port} échouée : {exc}")
            return

        self.status.emit(f"Connecté à {self._port} @ {self._baudrate} bauds")

        consecutive_errors = 0
        last_rate_ts = time.monotonic()
        samples_since_tick = 0

        try:
            while not self._stop_requested:
                # 1) commandes en attente
                while not self._command_queue.empty():
                    try:
                        name, arg = self._command_queue.get_nowait()
                        self._dispatch_command(name, arg)
                    except queue.Empty:
                        break
                    except Exception as exc:
                        self.status.emit(f"Commande {name} échouée : {exc}")

                # 2) lecture d'un échantillon
                try:
                    mass_kg = self._device.read_weight_kg()
                    consecutive_errors = 0
                except (CRCError, ModbusTimeoutError, IOError) as exc:
                    consecutive_errors += 1
                    if consecutive_errors >= 5:
                        self.connection_lost.emit(f"Communication perdue : {exc}")
                        break
                    continue

                now = time.monotonic()
                if self._t0 is None:
                    self._t0 = now
                t_rel = now - self._t0
                force_n = mass_kg * G0

                self._buffer.append((t_rel, force_n))
                self.sample.emit(t_rel, force_n)

                # 3) mesure de la fréquence ~1 fois par seconde
                samples_since_tick += 1
                if now - last_rate_ts >= 1.0:
                    hz = samples_since_tick / (now - last_rate_ts)
                    self.rate.emit(hz)
                    samples_since_tick = 0
                    last_rate_ts = now
        finally:
            try:
                if self._device is not None:
                    self._device.close()
            except Exception:
                pass
            self.status.emit("Déconnecté")

    def _dispatch_command(self, name, arg):
        if self._device is None:
            return
        if name == "tare":
            self._device.tare()
            self.status.emit("Tare effectuée")
        elif name == "cancel_tare":
            self._device.cancel_tare()
            self.status.emit("Tare annulée")
        elif name == "set_filter":
            self._device.set_filter(arg)
            self.status.emit(f"Filtre = {arg}")
        elif name == "set_speed":
            self._device.set_speed(arg)
            self.status.emit(f"Vitesse = {arg}")
        elif name == "calibrate_lower":
            self._device.calibrate_lower()
            self.status.emit("Calibration zéro envoyée")
        elif name == "calibrate_upper":
            self._device.calibrate_upper()
            self.status.emit("Calibration haute envoyée")


def export_csv(path, samples, unit="N"):
    """
    samples : liste de tuples (t_rel, force_n).
    Écrit toutes les valeurs en une fois (flush garanti à la fermeture du with).
    """
    factor = 1.0 if unit == "N" else 1.0 / G0  # kgf
    header = ["time_s", "force_N" if unit == "N" else "force_kgf"]
    with open(path, "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(header)
        for t, f in samples:
            w.writerow([f"{t:.4f}", f"{f * factor:.4f}"])
