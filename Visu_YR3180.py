import sys
import time
import collections
import numpy as np

# On utilise PySide6 (l'interface Qt moderne)
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, Signal
import pyqtgraph as pg

from yr3180 import YR3180

class SensorReaderThread(QThread):
    """
    Thread dédié à la lecture du capteur pour ne pas bloquer l'interface
    et garantir un échantillonnage le plus précis possible.
    """
    new_data = Signal(float, float)  # timestamp, valeur_poids
    error_signal = Signal(str)

    def __init__(self, port, baudrate, slave_address=1, target_hz=100):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.slave_address = slave_address
        self.target_hz = target_hz
        self.interval = 1.0 / self.target_hz
        self._running = False
        
    def run(self):
        self._running = True
        try:
            # On instancie la classe de communication existante
            sensor = YR3180(port=self.port, baudrate=self.baudrate, slave_address=self.slave_address)
            # On réduit le timeout matériel du port série pour la réactivité (ex: 50ms max)
            sensor.serial.timeout = 0.05 
        except Exception as e:
            self.error_signal.emit(f"Erreur de connexion au port {self.port} : {e}")
            return
            
        start_time = time.perf_counter()
        next_call = start_time
        
        while self._running:
            try:
                # Lecture Modbus du poids. 
                # Rappel : À 9600 baud, 1 requête+réponse Modbus RTU prend ~20ms, donc 100Hz = impossible (max ~40-50Hz).
                # Pour obtenir 100Hz réel, il faut utiliser un baudrate de 115200.
                val = sensor.read_weight_float()
                
                # Timestamp relatif (secondes)
                t = time.perf_counter() - start_time
                self.new_data.emit(t, val)
                
            except Exception as e:
                # En cas de micro-coupure ou de trame corrompue, on l'Affiche discrètement (ou l'ignore) pour ne pas planter le thread
                print(f"Avertissement (Trame ignorée) : {e}")
                
            # Logique d'attente "précise" pour respecter scrupuleusement les 100 Hz
            next_call += self.interval
            sleep_time = next_call - time.perf_counter()
            
            # Pour une micro-précision sur Windows : petit `sleep(OS)` + boucle `while` active sur les 2 dernières millisecondes
            if sleep_time > 0.002:
                time.sleep(sleep_time - 0.002)
                while time.perf_counter() < next_call:
                    pass
            elif sleep_time > 0:
                while time.perf_counter() < next_call:
                    pass
            elif sleep_time < -self.interval:
                # Si on a pris du retard matériel (baudrate trop lent), on resynchronise 
                # pour éviter de boucler sans pause et faire crasher le CPU
                next_call = time.perf_counter()
                
        # Nettoyage
        try:
            sensor.close()
        except:
            pass

    def stop(self):
        """Demande l'arrêt du thread de façon ordonnée"""
        self._running = False
        self.wait()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualisation YR-3180 - Haute Fréquence")
        self.resize(1100, 700)
        
        # Buffer circulaire des données pour l'historique de la courbe.
        # Ex: 10 secondes affichées (10 * 100Hz = 1000 points)
        self.max_points = 1000
        self.time_data = collections.deque(maxlen=self.max_points)
        self.weight_data = collections.deque(maxlen=self.max_points)
        
        # Interface principale
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)
        
        # ---- Panneau de contrôle (Bande supérieure) ----
        control_layout = QtWidgets.QHBoxLayout()
        
        self.port_input = QtWidgets.QLineEdit("COM5")
        self.port_input.setFixedWidth(80)
        
        self.baud_combo = QtWidgets.QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        # On présélectionne 115200 pour sensibiliser à la vitesse Modbus requise pour 100Hz
        self.baud_combo.setCurrentText("115200") 
        self.baud_combo.setToolTip("Attention: 100 Hz est matériellement impossible à 9600 baud. Utilisez 115200 baud.")
        
        self.hz_input = QtWidgets.QSpinBox()
        self.hz_input.setRange(1, 200)
        self.hz_input.setValue(100)
        self.hz_input.setSuffix(" Hz")
        
        self.start_btn = QtWidgets.QPushButton("▶ Démarrer")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        
        self.stop_btn = QtWidgets.QPushButton("⏹ Arrêter")
        self.stop_btn.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 6px;")
        self.stop_btn.setEnabled(False)
        
        self.val_label = QtWidgets.QLabel("Poids: --- kg")
        self.val_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #1565C0;")
        
        self.real_freq_label = QtWidgets.QLabel("Fréq. réelle: --- Hz")
        self.real_freq_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #757575;")
        
        # Assemblage des boutons & text inputs
        control_layout.addWidget(QtWidgets.QLabel("Port :"))
        control_layout.addWidget(self.port_input)
        control_layout.addWidget(QtWidgets.QLabel("Baudrate :"))
        control_layout.addWidget(self.baud_combo)
        control_layout.addWidget(QtWidgets.QLabel("Vitesse Cible :"))
        control_layout.addWidget(self.hz_input)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()  # Espace élastique au milieu
        control_layout.addWidget(self.real_freq_label)
        control_layout.addSpacing(20)
        control_layout.addWidget(self.val_label)
        
        # Avertissement dynamique informatif 
        warning_label = QtWidgets.QLabel("⚠️ Physique de transfert : Pour 100 Hz réels (10ms), le Modbus doit lire en ~2 à 3ms. Votre module DOIT être réglé sur un Baudrate de 115200.")
        warning_label.setStyleSheet("color: #E65100; font-style: italic; font-size: 13px;")
        warning_label.setAlignment(QtCore.Qt.AlignCenter)
        
        layout.addLayout(control_layout)
        layout.addWidget(warning_label)
        
        # ---- Graphique (PyQtGraph) ----
        pg.setConfigOptions(antialias=True, background='w', foreground='k')
        self.plot_widget = pg.PlotWidget(title="Mesure de Force dynamique")
        
        # Style des axes et de la grille
        self.plot_widget.setLabel('left', 'Poids', units='kg', **{'font-size':'12pt', 'color':'black'})
        self.plot_widget.setLabel('bottom', 'Temps Relatif', units='s', **{'font-size':'12pt', 'color':'black'})
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setPen('k')
        self.plot_widget.getAxis('bottom').setPen('k')
        
        # Configuration de la ligne du graphe (Bleu épais, beau rendu)
        pen = pg.mkPen(color='#1976D2', width=2.5)
        # La courbe
        self.curve = self.plot_widget.plot(pen=pen, name="Poids (kg)")
        
        layout.addWidget(self.plot_widget)
        
        # ---- Logique & Timers ----
        self.reader_thread = None
        
        # On met à jour l'Interface à 30 IPS pour ne pas consommer du CPU inutilement à dessiner le graphe
        # (Les données matérielles restent acquises à 100 Hz en tâche de fond)
        self.ui_timer = QtCore.QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.setInterval(33) # 33ms = ~30 FPS
        
        # Branchement des actions
        self.start_btn.clicked.connect(self.start_acq)
        self.stop_btn.clicked.connect(self.stop_acq)
        
        # Variables de comptage des fréquences
        self.last_t = time.perf_counter()
        self.sample_count = 0
        self.last_poids = 0.0

    def start_acq(self):
        port = self.port_input.text().strip()
        baudrate = int(self.baud_combo.currentText())
        target_hz = self.hz_input.value()
        
        # Remet le graphe à zéro
        self.time_data.clear()
        self.weight_data.clear()
        self.sample_count = 0
        self.last_t = time.perf_counter()
        
        # Lance le thread de lecture (Thread isolé => pas de ralentissement d'interface)
        self.reader_thread = SensorReaderThread(port, baudrate, target_hz=target_hz)
        self.reader_thread.new_data.connect(self.on_new_data)
        self.reader_thread.error_signal.connect(self.on_error)
        self.reader_thread.start()
        
        # Lance le rafraichissement du graphe
        self.ui_timer.start()
        
        # Update les boutons
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.port_input.setEnabled(False)
        self.baud_combo.setEnabled(False)
        self.hz_input.setEnabled(False)

    def stop_acq(self):
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread = None
            
        self.ui_timer.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.port_input.setEnabled(True)
        self.baud_combo.setEnabled(True)
        self.hz_input.setEnabled(True)
        
    def on_new_data(self, t, val):
        # Cette fonction s'exécute quand le thread Modbus émet un nouveau point
        self.time_data.append(t)
        self.weight_data.append(val)
        self.sample_count += 1
        self.last_poids = val

    def on_error(self, err_msg):
        self.stop_acq()
        QtWidgets.QMessageBox.critical(self, "Erreur Connectivité", err_msg)

    def update_ui(self):
        """ Rafraîchissement graphique uniquement """
        # 1. Mise à jour de la courbe (Tracé de masse ultra-rapide avec NumPy)
        if len(self.time_data) > 0:
            # np.array convertit la pile deque instantanément pour pyqtgraph
            self.curve.setData(np.array(self.time_data), np.array(self.weight_data))
            
            # Formate avec 3 chiffres après la virgule
            self.val_label.setText(f"Poids: {self.last_poids:.3f} kg")
            
        # 2. Calculer le Taux d'échantillonnage réel (Fréquence Hardware) toutes les secondes
        now = time.perf_counter()
        dt = now - self.last_t
        if dt >= 1.0:
            real_freq = self.sample_count / dt
            
            # Affiche en rouge l'indication s'il y a plus de 10% d'écart matériel avec l'attente 100Hz
            target = self.hz_input.value()
            if abs(real_freq - target) > (target * 0.1):
                self.real_freq_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #D32F2F;") # Rouge warning
            else:
                self.real_freq_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388E3C;") # Vert ok
                
            self.real_freq_label.setText(f"Fréq. réelle: {real_freq:.1f} Hz")
            
            self.sample_count = 0
            self.last_t = now

    def closeEvent(self, event):
        # En quittant l'app, on stoppe proprement pour libérer COM5
        self.stop_acq()
        event.accept()

if __name__ == '__main__':
    # Initialisation application moderne QT
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Prise en compte du scaling des écrans Haute Définition (4K, Laptops Windows 150%...)
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
