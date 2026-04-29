import sys
import time
import struct
import datetime
import csv
import collections
import numpy as np
import os

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QThread, Signal
import pyqtgraph as pg

from yr3180 import YR3180

# Constante de conversion kg -> Newton
KG_TO_N = 9.80665

class SensorReaderThread(QThread):
    new_data = Signal(float, float)  # timestamp, valeur_poids (en kg bruts)
    log_signal = Signal(str)         # pour la console
    error_signal = Signal(str)

    def __init__(self, port, baudrate, slave_address=1, target_hz=100, record_file=None):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.slave_address = slave_address
        self.target_hz = target_hz
        self.interval = 1.0 / self.target_hz
        self._running = False
        self.record_file = record_file
        self.sensor = None

    def run(self):
        self._running = True
        try:
            self.sensor = YR3180(port=self.port, baudrate=self.baudrate, slave_address=self.slave_address)
            self.sensor.serial.timeout = 0.5 # Timeout augmenté pour éviter les lectures trop courtes
            self.log_signal.emit(f"Port {self.port} ouvert à {self.baudrate} baud.")
            time.sleep(0.5) # Laisser le temps au port série/USB de se stabiliser
        except Exception as e:
            self.error_signal.emit(f"Erreur d'ouverture du port {self.port} : {e}")
            return
            
        # --- VERIFICATION DE LA CONNEXION ---
        try:
            self.log_signal.emit("Test de communication avec le capteur...")
            test_val = self.sensor.read_weight_float()
            self.log_signal.emit(f"✅ Succès : Capteur YR-3180 répond correctement. (Poids lu: {test_val:.2f} kg)")
        except ValueError as ve:
            self.log_signal.emit(f"❌ Échec de communication. Détails : {ve}")
            self.error_signal.emit(f"Le capteur ne répond pas correctement. Détails : {ve}")
            self._running = False
            return
        except Exception as e:
            self.log_signal.emit(f"❌ Échec de la communication : {e}")
            self.error_signal.emit(f"Erreur de communication : {e}")
            self._running = False
            return
        # ------------------------------------

        start_time = time.perf_counter()
        next_call = start_time
        
        bin_file = None
        if self.record_file:
            try:
                bin_file = open(self.record_file, "wb")
                self.log_signal.emit(f"Enregistrement binaire démarré: {self.record_file}")
            except Exception as e:
                self.error_signal.emit(f"Erreur d'ouverture du fichier d'enregistrement : {e}")
                self._running = False
        
        error_count = 0
        while self._running:
            try:
                val_kg = self.sensor.read_weight_float()
                t = time.perf_counter() - start_time
                
                if bin_file:
                    bin_file.write(struct.pack('<dd', t, val_kg))
                
                self.new_data.emit(t, val_kg)
                error_count = 0 # reset on success
                
            except ValueError as ve:
                error_count += 1
                if error_count == 1:
                    # Ne logger la perte que la première fois pour éviter de spammer la console à 100Hz
                    self.log_signal.emit("⚠️ Trame ignorée ou perdue (timeout ou erreur CRC).")
            except Exception as e:
                pass
                
            next_call += self.interval
            sleep_time = next_call - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_call = time.perf_counter()

        if bin_file:
            bin_file.close()
            self.log_signal.emit(f"Fichier d'enregistrement fermé.")
            
        if self.sensor:
            try:
                self.sensor.close()
                self.log_signal.emit("Port série fermé proprement.")
            except:
                pass

    def stop(self):
        self._running = False
        self.wait()

    def tare(self):
        if self.sensor and self._running:
            try:
                self.log_signal.emit("Envoi de la commande TARE...")
                self.sensor.tare()
                self.log_signal.emit("✅ TARE effectuée avec succès.")
            except Exception as e:
                self.log_signal.emit(f"❌ Erreur lors de la TARE: {e}")

def extract_bin_to_csv(bin_path):
    if not os.path.exists(bin_path):
        return False
    csv_path = bin_path.replace('.bin', '.csv')
    try:
        with open(bin_path, 'rb') as bf, open(csv_path, 'w', newline='') as cf:
            writer = csv.writer(cf)
            writer.writerow(['Time (s)', 'Weight (kg)', 'Thrust (N)'])
            while True:
                data = bf.read(16)
                if len(data) < 16:
                    break
                t, val_kg = struct.unpack('<dd', data)
                writer.writerow([f"{t:.4f}", f"{val_kg:.4f}", f"{val_kg * KG_TO_N:.4f}"])
        return csv_path
    except Exception as e:
        return None

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Thrust Dashboard YR-3180")
        self.resize(1200, 800)
        
        # VRAI Dark Mode (Noir profond, accentuations vertes/rouges)
        self.setStyleSheet("""
            QMainWindow { background-color: #0A0A0A; }
            QLabel { color: #FFFFFF; font-family: 'Segoe UI', Arial; }
            QGroupBox { border: 1px solid #333333; border-radius: 8px; margin-top: 15px; color: #888888; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 15px; color: #FFFFFF; }
            QPushButton { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #444444; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #2A2A2A; border: 1px solid #666666; }
            QPushButton:pressed { background-color: #000000; }
            QPushButton:disabled { background-color: #111111; color: #555555; border: 1px solid #222222; }
            QLineEdit, QComboBox, QSpinBox { background-color: #151515; color: #00E676; border: 1px solid #333333; padding: 5px; border-radius: 3px; font-weight: bold; }
            QCheckBox { color: #FFFFFF; font-weight: bold; }
            QTextEdit { background-color: #050505; color: #00E676; font-family: 'Consolas', monospace; border: 1px solid #222222; border-radius: 5px; padding: 5px; }
        """)

        self.max_points = 500
        self.time_data = collections.deque(maxlen=self.max_points)
        self.weight_data = collections.deque(maxlen=self.max_points)
        
        self.is_newton = True
        self.peak_value = 0.0
        
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal vertical
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        
        # Top layout: Gauche (Boutons/Infos) | Droite (Graphe)
        top_layout = QtWidgets.QHBoxLayout()
        
        # --- PANNEAU GAUCHE ---
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setContentsMargins(5, 5, 10, 5)
        
        # 1. Indicateurs Géants
        indicator_group = QtWidgets.QGroupBox("MESURES")
        ind_layout = QtWidgets.QVBoxLayout()
        
        self.current_label = QtWidgets.QLabel("0.00 N")
        self.current_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_label.setStyleSheet("font-size: 55px; font-weight: bold; color: #00E676; background-color: #111111; border: 2px solid #00E676; border-radius: 8px; padding: 15px;") 
        
        self.peak_label = QtWidgets.QLabel("MAX: 0.00 N")
        self.peak_label.setAlignment(QtCore.Qt.AlignCenter)
        self.peak_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #FF5252; background-color: #111111; border: 2px solid #FF5252; border-radius: 8px; padding: 8px;") 
        
        self.unit_toggle_btn = QtWidgets.QPushButton("Unité Actuelle : NEWTONS")
        self.unit_toggle_btn.setStyleSheet("background-color: #0D47A1; color: white; font-size: 14px; border: none;")
        self.unit_toggle_btn.clicked.connect(self.toggle_unit)
        
        self.tare_btn = QtWidgets.QPushButton("TARE (ZÉRO)")
        self.tare_btn.setStyleSheet("background-color: #E65100; color: white; font-size: 18px; padding: 15px; border: none;")
        self.tare_btn.clicked.connect(self.do_tare)
        
        ind_layout.addWidget(QtWidgets.QLabel("Poussée Actuelle :"))
        ind_layout.addWidget(self.current_label)
        ind_layout.addSpacing(10)
        ind_layout.addWidget(QtWidgets.QLabel("Poussée Maximale :"))
        ind_layout.addWidget(self.peak_label)
        ind_layout.addSpacing(20)
        ind_layout.addWidget(self.unit_toggle_btn)
        ind_layout.addWidget(self.tare_btn)
        indicator_group.setLayout(ind_layout)
        
        # 2. Contrôle Acquisition
        acq_group = QtWidgets.QGroupBox("ACQUISITION")
        acq_layout = QtWidgets.QFormLayout()
        
        self.port_input = QtWidgets.QLineEdit("COM5")
        self.baud_combo = QtWidgets.QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        
        self.hz_input = QtWidgets.QSpinBox()
        self.hz_input.setRange(1, 200)
        self.hz_input.setValue(100)
        
        self.rec_checkbox = QtWidgets.QCheckBox("Enregistrer (.bin)")
        self.rec_checkbox.setChecked(True)
        
        acq_layout.addRow("Port:", self.port_input)
        acq_layout.addRow("Baudrate:", self.baud_combo)
        acq_layout.addRow("Fréq (Hz):", self.hz_input)
        acq_layout.addRow("", self.rec_checkbox)
        
        self.start_btn = QtWidgets.QPushButton("▶ DÉMARRER")
        self.start_btn.setStyleSheet("background-color: #1B5E20; color: white; font-size: 16px; border: none;")
        self.start_btn.clicked.connect(self.start_acq)
        
        self.stop_btn = QtWidgets.QPushButton("⏹ ARRÊTER")
        self.stop_btn.setStyleSheet("background-color: #B71C1C; color: white; font-size: 16px; border: none;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_acq)
        
        self.extract_btn = QtWidgets.QPushButton("Extraire CSV depuis .bin")
        self.extract_btn.clicked.connect(self.extract_csv)
        
        acq_layout.addRow(self.start_btn)
        acq_layout.addRow(self.stop_btn)
        acq_layout.addRow(QtWidgets.QLabel(""))
        acq_layout.addRow(self.extract_btn)
        acq_group.setLayout(acq_layout)
        
        left_panel.addWidget(indicator_group)
        left_panel.addWidget(acq_group)
        left_panel.addStretch()
        
        # --- PANNEAU DROITE (Graphe) ---
        pg.setConfigOptions(antialias=True, background='#050505', foreground='#FFFFFF')
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Poussée', units='N', **{'font-size':'14pt'})
        self.plot_widget.setLabel('bottom', 'Temps Relatif', units='s', **{'font-size':'14pt'})
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setPen('#444444')
        self.plot_widget.getAxis('bottom').setPen('#444444')
        
        # Pen Neon Cyan
        pen = pg.mkPen(color='#00E5FF', width=3)
        self.curve = self.plot_widget.plot(pen=pen, fillLevel=0, brush=(0, 229, 255, 30))
        
        # Assemblage Top Layout (Gauche = 1 part, Droite = 3 parts)
        top_layout.addLayout(left_panel, 1)
        top_layout.addWidget(self.plot_widget, 3)
        
        # --- CONSOLE EN BAS ---
        console_layout = QtWidgets.QVBoxLayout()
        console_label = QtWidgets.QLabel("💻 Console Système (Logs en direct)")
        console_label.setStyleSheet("color: #888888; font-weight: bold; margin-top: 10px;")
        
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(120)
        
        console_layout.addWidget(console_label)
        console_layout.addWidget(self.console)
        
        # Ajout au layout principal
        main_layout.addLayout(top_layout, 4)
        main_layout.addLayout(console_layout, 1)
        
        self.reader_thread = None
        self.ui_timer = QtCore.QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.setInterval(33) # ~30fps
        
        self.last_poids_kg = 0.0
        self.log_message("🚀 Thrust Dashboard initialisé. Prêt à démarrer.")

    def log_message(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console.append(f"[{ts}] {msg}")
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def toggle_unit(self):
        self.is_newton = not self.is_newton
        unit_str = "NEWTONS" if self.is_newton else "KILOGRAMMES"
        self.unit_toggle_btn.setText(f"Unité Actuelle : {unit_str}")
        
        if self.is_newton:
            self.plot_widget.setLabel('left', 'Poussée', units='N')
        else:
            self.plot_widget.setLabel('left', 'Poids', units='kg')
            
        self.update_display_values()

    def do_tare(self):
        if self.reader_thread:
            self.reader_thread.tare()
        else:
            self.log_message("⚠️ Impossible de faire la Tare : L'acquisition n'est pas démarrée.")
        self.peak_value = 0.0
        self.time_data.clear()
        self.weight_data.clear()
        self.update_display_values()

    def start_acq(self):
        port = self.port_input.text().strip()
        baudrate = int(self.baud_combo.currentText())
        target_hz = self.hz_input.value()
        
        self.time_data.clear()
        self.weight_data.clear()
        self.peak_value = 0.0
        self.update_display_values()
        
        record_file = None
        if self.rec_checkbox.isChecked():
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            record_file = f"test_motor_{timestamp_str}.bin"
            
        self.log_message(f"--- Nouvelle session sur {port} ---")
            
        self.reader_thread = SensorReaderThread(port, baudrate, target_hz=target_hz, record_file=record_file)
        self.reader_thread.new_data.connect(self.on_new_data)
        self.reader_thread.log_signal.connect(self.log_message)
        self.reader_thread.error_signal.connect(self.on_error)
        self.reader_thread.start()
        
        self.ui_timer.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.port_input.setEnabled(False)
        self.baud_combo.setEnabled(False)

    def stop_acq(self):
        if self.reader_thread:
            self.log_message("🛑 Demande d'arrêt envoyée...")
            self.reader_thread.stop()
            self.reader_thread = None
            
        self.ui_timer.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.port_input.setEnabled(True)
        self.baud_combo.setEnabled(True)

    def on_new_data(self, t, val_kg):
        self.last_poids_kg = val_kg
        val_display = val_kg * KG_TO_N if self.is_newton else val_kg
        
        if val_display > self.peak_value:
            self.peak_value = val_display
            
        self.time_data.append(t)
        self.weight_data.append(val_display)

    def on_error(self, err_msg):
        self.log_message(f"🚨 ERREUR CRITIQUE: {err_msg}")
        self.stop_acq()
        QtWidgets.QMessageBox.critical(self, "Erreur", err_msg)

    def update_ui(self):
        if len(self.time_data) > 0:
            self.curve.setData(np.array(self.time_data), np.array(self.weight_data))
            self.update_display_values()

    def update_display_values(self):
        val = self.last_poids_kg * KG_TO_N if self.is_newton else self.last_poids_kg
        unit = "N" if self.is_newton else "kg"
        
        self.current_label.setText(f"{val:.2f} {unit}")
        self.peak_label.setText(f"MAX: {self.peak_value:.2f} {unit}")

    def extract_csv(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Sélectionner un fichier binaire", "", "Binary Files (*.bin)")
        if file_path:
            self.log_message(f"Extraction de {file_path} vers CSV en cours...")
            csv_path = extract_bin_to_csv(file_path)
            if csv_path:
                self.log_message(f"✅ Extraction réussie : {csv_path}")
                QtWidgets.QMessageBox.information(self, "Succès", f"Fichier extrait avec succès :\n{csv_path}")
            else:
                self.log_message("❌ Échec de l'extraction.")
                QtWidgets.QMessageBox.warning(self, "Erreur", "Impossible d'extraire le fichier.")

    def closeEvent(self, event):
        self.stop_acq()
        event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
