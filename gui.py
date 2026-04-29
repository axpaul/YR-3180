# -------------------------------------------------------------
# Fichier : gui.py
# Objet   : Interface graphique du banc de poussée (PySide6 + pyqtgraph).
#           Lance avec : python gui.py
# -------------------------------------------------------------

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from acquisition import AcquisitionWorker, export_csv, G0
from analysis import format_report, summarize

CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_CONFIG = {
    "port": "",
    "baudrate": 9600,
    "unit": "N",
    "auto_trigger_threshold_n": 2.0,
    "export_dir": str(Path.home()),
    "plot_window_s": 10.0,
    "propellant_mass_g": 0.0,
}


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fp:
                cfg = json.load(fp)
            return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fp:
            json.dump(cfg, fp, indent=2)
    except Exception:
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Banc de poussée YR-3180")
        self.resize(1200, 700)

        self.config = load_config()
        self.worker: AcquisitionWorker | None = None

        # buffer pour le live plot (uniquement la fenêtre visible)
        self._plot_t: list[float] = []
        self._plot_f: list[float] = []

        # buffer d'enregistrement (REC actif)
        self._record_t: list[float] = []
        self._record_f: list[float] = []
        self._recording = False
        self._auto_trigger = False
        self._below_threshold_since: float | None = None

        self._build_ui()
        self._refresh_ports()

        # rafraîchissement du plot à 30 fps
        self._plot_timer = QTimer(self)
        self._plot_timer.setInterval(33)
        self._plot_timer.timeout.connect(self._refresh_plot)
        self._plot_timer.start()

    # ---------------- Construction UI ----------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # --- Colonne gauche : panneaux ---
        left = QVBoxLayout()
        left.addWidget(self._build_connection_box())
        left.addWidget(self._build_measure_box())
        left.addWidget(self._build_controls_box())
        left.addStretch(1)

        # --- Plot ---
        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")
        self.plot.setLabel("left", "Force", units="N")
        self.plot.setLabel("bottom", "Temps", units="s")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.curve = self.plot.plot(pen=pg.mkPen("#1976d2", width=2))
        self.peak_marker = pg.ScatterPlotItem(
            size=12, brush=pg.mkBrush("#d32f2f"), pen=pg.mkPen(None)
        )
        self.plot.addItem(self.peak_marker)
        self.threshold_line = pg.InfiniteLine(
            angle=0, pen=pg.mkPen("#9e9e9e", style=Qt.DashLine),
            movable=False,
        )
        self.threshold_line.setValue(self.config["auto_trigger_threshold_n"])
        self.plot.addItem(self.threshold_line)

        root.addLayout(left, 0)
        root.addWidget(self.plot, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Prêt — sélectionnez un port et connectez-vous.")

    def _build_connection_box(self):
        box = QGroupBox("Connexion")
        f = QFormLayout(box)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setMaximumWidth(32)
        self.refresh_btn.clicked.connect(self._refresh_ports)
        port_row = QHBoxLayout()
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(self.refresh_btn)
        port_widget = QWidget()
        port_widget.setLayout(port_row)
        f.addRow("Port :", port_widget)

        self.baud_combo = QComboBox()
        for b in (9600, 19200, 38400, 57600, 115200):
            self.baud_combo.addItem(str(b), b)
        idx = self.baud_combo.findData(self.config["baudrate"])
        if idx >= 0:
            self.baud_combo.setCurrentIndex(idx)
        f.addRow("Baudrate :", self.baud_combo)

        self.connect_btn = QPushButton("Connecter")
        self.connect_btn.clicked.connect(self._toggle_connection)
        f.addRow(self.connect_btn)

        return box

    def _build_measure_box(self):
        box = QGroupBox("Mesure")
        v = QVBoxLayout(box)

        big = QFont()
        big.setPointSize(22)
        big.setBold(True)

        self.lbl_force = QLabel("—")
        self.lbl_force.setFont(big)
        self.lbl_force.setAlignment(Qt.AlignCenter)
        v.addWidget(self.lbl_force)

        f = QFormLayout()
        self.lbl_peak = QLabel("—")
        self.lbl_duration = QLabel("—")
        self.lbl_impulse = QLabel("—")
        self.lbl_avg = QLabel("—")
        f.addRow("Pic :", self.lbl_peak)
        f.addRow("Durée :", self.lbl_duration)
        f.addRow("Impulsion :", self.lbl_impulse)
        f.addRow("Moyenne :", self.lbl_avg)
        v.addLayout(f)

        self.unit_check = QCheckBox("Afficher en kgf (au lieu de N)")
        self.unit_check.setChecked(self.config["unit"] == "kgf")
        self.unit_check.toggled.connect(self._on_unit_toggled)
        v.addWidget(self.unit_check)

        return box

    def _build_controls_box(self):
        box = QGroupBox("Contrôles")
        v = QVBoxLayout(box)

        self.tare_btn = QPushButton("Tare")
        self.tare_btn.clicked.connect(self._on_tare)
        self.tare_btn.setEnabled(False)
        v.addWidget(self.tare_btn)

        self.rec_btn = QPushButton("▶ Démarrer enregistrement")
        self.rec_btn.setCheckable(True)
        self.rec_btn.clicked.connect(self._on_rec_toggled)
        self.rec_btn.setEnabled(False)
        v.addWidget(self.rec_btn)

        self.export_btn = QPushButton("Exporter CSV + rapport")
        self.export_btn.clicked.connect(self._on_export)
        self.export_btn.setEnabled(False)
        v.addWidget(self.export_btn)

        self.clear_btn = QPushButton("Réinitialiser buffer")
        self.clear_btn.clicked.connect(self._on_clear)
        self.clear_btn.setEnabled(False)
        v.addWidget(self.clear_btn)

        # Auto-trigger
        trig = QFormLayout()
        self.auto_check = QCheckBox("Auto-trigger")
        self.auto_check.toggled.connect(self._on_auto_toggled)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1000.0)
        self.threshold_spin.setSuffix(" N")
        self.threshold_spin.setValue(self.config["auto_trigger_threshold_n"])
        self.threshold_spin.valueChanged.connect(self._on_threshold_changed)
        trig.addRow(self.auto_check)
        trig.addRow("Seuil :", self.threshold_spin)
        v.addLayout(trig)

        # Réglages capteur
        sensor = QFormLayout()
        self.filter_spin = QSpinBox()
        self.filter_spin.setRange(0, 9)
        self.filter_spin.setValue(1)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 9)
        self.speed_spin.setValue(5)
        self.apply_sensor_btn = QPushButton("Appliquer")
        self.apply_sensor_btn.clicked.connect(self._on_apply_sensor)
        self.apply_sensor_btn.setEnabled(False)
        sensor.addRow("Filtre :", self.filter_spin)
        sensor.addRow("Vitesse :", self.speed_spin)
        sensor.addRow(self.apply_sensor_btn)
        v.addLayout(sensor)

        return box

    # ---------------- Connexion ----------------

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        for p in list_ports.comports():
            label = f"{p.device} — {p.description}"
            self.port_combo.addItem(label, p.device)
        # restaurer la sélection précédente ou celle du config
        target = current or self.config.get("port") or ""
        if target:
            for i in range(self.port_combo.count()):
                if self.port_combo.itemData(i) == target or target in self.port_combo.itemText(i):
                    self.port_combo.setCurrentIndex(i)
                    return
            self.port_combo.setEditText(target)

    def _selected_port(self):
        data = self.port_combo.currentData()
        if data:
            return data
        # texte libre (au cas où l'utilisateur tape COM7 manuellement)
        text = self.port_combo.currentText().strip()
        return text.split(" ")[0] if text else ""

    def _toggle_connection(self):
        if self.worker is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self):
        port = self._selected_port()
        if not port:
            QMessageBox.warning(self, "Port", "Aucun port sélectionné.")
            return
        baud = self.baud_combo.currentData()

        self.worker = AcquisitionWorker(port=port, baudrate=baud)
        self.worker.sample.connect(self._on_sample)
        self.worker.connection_lost.connect(self._on_connection_lost)
        self.worker.status.connect(lambda m: self.statusBar().showMessage(m))
        self.worker.rate.connect(self._on_rate)
        self.worker.start()

        self.connect_btn.setText("Déconnecter")
        self.tare_btn.setEnabled(True)
        self.rec_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.apply_sensor_btn.setEnabled(True)

        self.config["port"] = port
        self.config["baudrate"] = baud
        save_config(self.config)

    def _disconnect(self):
        if self.worker is None:
            return
        self.worker.stop()
        self.worker.wait(2000)
        self.worker = None

        self.connect_btn.setText("Connecter")
        self.tare_btn.setEnabled(False)
        self.rec_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.apply_sensor_btn.setEnabled(False)
        self.statusBar().showMessage("Déconnecté")

    def _on_connection_lost(self, msg):
        QMessageBox.critical(self, "Connexion perdue", msg)
        self._disconnect()

    def _on_rate(self, hz):
        # juxtaposé au message courant via setStatusTip ne marche pas, on
        # remplace le message avec un tag fréquence.
        existing = self.statusBar().currentMessage().split(" · ")[0]
        n = len(self._record_t)
        self.statusBar().showMessage(f"{existing} · {hz:.0f} Hz · buffer enreg. : {n} pts")

    # ---------------- Réception samples ----------------

    def _on_sample(self, t_rel, force_n):
        self._plot_t.append(t_rel)
        self._plot_f.append(force_n)
        # ne garder que la fenêtre visible (~600 pts à 60 Hz x 10 s)
        window = self.config["plot_window_s"]
        cutoff = t_rel - window
        if self._plot_t and self._plot_t[0] < cutoff:
            # tronquage en O(n) mais peu fréquent ; suffisant pour 60-100 Hz
            i = 0
            while i < len(self._plot_t) and self._plot_t[i] < cutoff:
                i += 1
            del self._plot_t[:i]
            del self._plot_f[:i]

        # auto-trigger
        if self._auto_trigger:
            threshold = self.threshold_spin.value()
            if not self._recording and force_n > threshold:
                self._start_recording()
            elif self._recording:
                if force_n < threshold:
                    if self._below_threshold_since is None:
                        self._below_threshold_since = t_rel
                    elif t_rel - self._below_threshold_since >= 0.5:
                        self._stop_recording()
                else:
                    self._below_threshold_since = None

        if self._recording:
            self._record_t.append(t_rel)
            self._record_f.append(force_n)

        # mise à jour des chiffres en direct (pas dans le timer pour rester réactif)
        unit_factor, unit_label = self._unit()
        self.lbl_force.setText(f"{force_n * unit_factor:+7.2f} {unit_label}")

    # ---------------- Refresh visuel ----------------

    def _refresh_plot(self):
        if not self._plot_t:
            return
        unit_factor, unit_label = self._unit()
        t = np.asarray(self._plot_t)
        f = np.asarray(self._plot_f) * unit_factor
        self.curve.setData(t, f)
        self.plot.setLabel("left", "Force", units=unit_label)
        self.threshold_line.setValue(self.threshold_spin.value() * unit_factor)

        # statistiques sur le buffer d'enregistrement
        if self._record_t:
            tt = np.asarray(self._record_t)
            ff = np.asarray(self._record_f)
            s = summarize(
                tt, ff,
                threshold_n=self.threshold_spin.value(),
                propellant_mass_kg=self.config["propellant_mass_g"] / 1000.0,
            )
            self.lbl_peak.setText(f"{s['peak_n'] * unit_factor:.2f} {unit_label}")
            self.lbl_duration.setText(
                f"{s['duration_s']:.3f} s" if s['duration_s'] > 0 else "—"
            )
            self.lbl_impulse.setText(f"{s['impulse_ns']:.2f} N·s")
            self.lbl_avg.setText(f"{s['average_n'] * unit_factor:.2f} {unit_label}")

            if s['t_peak'] is not None:
                self.peak_marker.setData(
                    [s['t_peak']], [s['peak_n'] * unit_factor]
                )
            else:
                self.peak_marker.clear()
        else:
            self.peak_marker.clear()

    def _unit(self):
        if self.unit_check.isChecked():
            return 1.0 / G0, "kgf"
        return 1.0, "N"

    # ---------------- Slots boutons ----------------

    def _on_tare(self):
        if self.worker:
            self.worker.request_tare()

    def _on_rec_toggled(self, checked):
        if checked:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self._recording = True
        self._record_t.clear()
        self._record_f.clear()
        self._below_threshold_since = None
        self.rec_btn.setChecked(True)
        self.rec_btn.setText("■ Arrêter enregistrement")

    def _stop_recording(self):
        self._recording = False
        self.rec_btn.setChecked(False)
        self.rec_btn.setText("▶ Démarrer enregistrement")
        self._below_threshold_since = None

    def _on_clear(self):
        self._record_t.clear()
        self._record_f.clear()
        self._plot_t.clear()
        self._plot_f.clear()
        self.lbl_peak.setText("—")
        self.lbl_duration.setText("—")
        self.lbl_impulse.setText("—")
        self.lbl_avg.setText("—")
        if self.worker:
            self.worker.clear_buffer()

    def _on_export(self):
        if not self._record_t:
            QMessageBox.information(
                self, "Export", "Le buffer d'enregistrement est vide."
            )
            return
        default_dir = self.config.get("export_dir") or str(Path.home())
        ts = time.strftime("%Y%m%d_%H%M%S")
        default_path = os.path.join(default_dir, f"tir_{ts}.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer CSV", default_path, "CSV (*.csv)"
        )
        if not path:
            return

        unit = "kgf" if self.unit_check.isChecked() else "N"
        samples = list(zip(self._record_t, self._record_f))
        export_csv(path, samples, unit=unit)

        # rapport texte associé
        s = summarize(
            np.asarray(self._record_t),
            np.asarray(self._record_f),
            threshold_n=self.threshold_spin.value(),
            propellant_mass_kg=self.config["propellant_mass_g"] / 1000.0,
        )
        report_path = os.path.splitext(path)[0] + "_rapport.txt"
        with open(report_path, "w", encoding="utf-8") as fp:
            fp.write(format_report(s, self.config["propellant_mass_g"] / 1000.0))

        self.config["export_dir"] = os.path.dirname(path)
        save_config(self.config)
        self.statusBar().showMessage(f"Exporté : {path}")

    def _on_auto_toggled(self, checked):
        self._auto_trigger = bool(checked)
        if not checked:
            self._below_threshold_since = None

    def _on_threshold_changed(self, value):
        self.config["auto_trigger_threshold_n"] = float(value)
        save_config(self.config)

    def _on_unit_toggled(self, checked):
        self.config["unit"] = "kgf" if checked else "N"
        save_config(self.config)

    def _on_apply_sensor(self):
        if not self.worker:
            return
        self.worker.request_set_filter(self.filter_spin.value())
        self.worker.request_set_speed(self.speed_spin.value())

    # ---------------- Fermeture ----------------

    def closeEvent(self, event):
        # flush garanti même si l'utilisateur ferme sans exporter
        if self._record_t:
            try:
                ts = time.strftime("%Y%m%d_%H%M%S")
                fallback = os.path.join(
                    self.config.get("export_dir") or str(Path.home()),
                    f"tir_{ts}_autosave.csv",
                )
                export_csv(fallback, list(zip(self._record_t, self._record_f)),
                           unit="N")
                self.statusBar().showMessage(f"Sauvegarde auto : {fallback}")
            except Exception:
                pass
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
        save_config(self.config)
        super().closeEvent(event)


def main():
    pg.setConfigOptions(antialias=True)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
