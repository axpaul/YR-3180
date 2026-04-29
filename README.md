# Banc de poussée YR-3180

Banc de mesure de poussée pour moteurs fusée à propulsion solide / hybride, basé sur le module de pesée numérique **YR-3180** (cellule de charge + ADC + Modbus RTU sur TTL).

L'objectif : mesurer en direct la force développée par un moteur pendant la combustion, en extraire les indicateurs habituels (pic, durée, impulsion totale, Isp), et logguer les données brutes pour analyse a posteriori.

![YR-3180 Front and Back View](https://github.com/axpaul/YR-3180/raw/main/Image/IMG_5954.JPEG)

---

## Sommaire

1. [Démarrage rapide](#démarrage-rapide)
2. [Interface graphique](#interface-graphique)
3. [Architecture du logiciel](#architecture-du-logiciel)
4. [Câblage matériel](#câblage-matériel)
5. [Calibration](#calibration)
6. [Référence YR-3180 (datasheet)](#référence-yr-3180-datasheet)
7. [Fichier CAO support](#fichier-cao-support)

---

## Démarrage rapide

### Pré-requis

- Python ≥ 3.10
- Module YR-3180 raccordé à un adaptateur USB-TTL 5 V (ex. [FTDI TTL-232R-5V-WE](https://ftdichip.com/products/ttl-232r-5v-we/))
- Cellule de charge câblée sur le module (E+/E-/INA+/INA-)

### Installation

```bash
git clone <ce-repo>
cd banc_pousse_paul
pip install -r requirements.txt
```

`requirements.txt` :

```
pyserial>=3.5
PySide6>=6.6
pyqtgraph>=0.13
numpy>=1.24
```

### Lancement

```bash
python gui.py
```

Au premier démarrage, l'interface scanne les ports série disponibles. Sélectionne le port (typiquement `COM7` sous Windows), choisis le baudrate (9600 par défaut, certains modules sont configurés en 115200), puis clique **Connecter**. Les réglages sont mémorisés dans `config.json`.

### Scripts CLI (debug / sans GUI)

| Script | Rôle |
|--------|------|
| [Demo-TTL.py](Demo-TTL.py) | Lecture unique en Modbus brut, sans la classe `YR3180`. Utile pour diagnostiquer une trame qui ne passe pas. |
| [Demo-read.py](Demo-read.py) | Logger CSV continu (équivalent CLI de la GUI, fréquence 100 Hz visée). |
| [test_all_commands.py](test_all_commands.py) | Lit tous les registres connus et affiche leur valeur — pratique après un reset. |
| [reset_config_yr3180.py](reset_config_yr3180.py) | Remet le capteur en configuration usine. |

---

## Interface graphique

L'interface est écrite en **PySide6 + pyqtgraph** pour permettre un live plot fluide (~60 fps) tout en pilotant le capteur dans un thread séparé.

```
┌─────────────────────────────────────────────────────────────┐
│  Banc de poussée YR-3180                                    │
├──────────────┬──────────────────────────────────────────────┤
│ Connexion    │                                              │
│ Port [COM7▼] │           LIVE PLOT (force vs temps)         │
│ Baud [9600▼] │           — fenêtre glissante 10 s            │
│ [Connecter]  │           — marqueur rouge sur le pic        │
│              │           — ligne pointillée = seuil         │
│ Mesure       │             d'auto-trigger                   │
│  +12.34 N    │                                              │
│ Pic   45.6 N │                                              │
│ Durée 0.84 s │                                              │
│ Impuls. 18.2 │                                              │
│ Moy.  21.7 N │                                              │
│              ├──────────────────────────────────────────────┤
│ [Tare]       │ Statut : Connecté · 67 Hz · buffer 1420 pts  │
│ [▶ REC]      │                                              │
│ [Export CSV] │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### Fonctionnalités

- **Live plot** : courbe force vs temps glissante sur 10 s (configurable), marqueur sur le pic en cours, ligne de seuil d'auto-trigger.
- **Tare** logicielle (envoie `tare()` au capteur sans interrompre l'acquisition).
- **Auto-trigger** : démarre automatiquement l'enregistrement quand la force dépasse un seuil (par défaut 2 N), s'arrête après 500 ms sous le seuil. Idéal pour un test fusée où on ne sait pas exactement quand l'allumage se produit.
- **Indicateurs en direct** sur le buffer d'enregistrement :
  - pic de poussée (avec instant)
  - durée de combustion (détectée par hystérésis sur le seuil)
  - poussée moyenne sur la fenêtre de combustion
  - impulsion totale ∫F·dt (intégration trapézoïdale)
  - impulsion spécifique Isp si la masse de propergol est renseignée dans `config.json` (`propellant_mass_g`)
- **Unités** : bascule N ↔ kgf en un clic (la conversion utilise g₀ = 9,80665 m/s²).
- **Export** : CSV des échantillons + fichier `_rapport.txt` lisible avec le récap du tir.
- **Autosave** : si la fenêtre est fermée pendant un enregistrement, un CSV `..._autosave.csv` est écrit dans le dossier d'export.
- **Reconnexion-friendly** : 5 erreurs Modbus consécutives → message « connexion perdue » plutôt que crash silencieux.
- **Persistance** : port, baudrate, seuil, dossier d'export et masse propergol sont mémorisés dans `config.json`.

### Réglages capteur depuis la GUI

Le panneau « Contrôles » expose :

- **Filtre** (registre 5, valeur 0–40) : filtrage moyenne glissante. Plus c'est haut, plus c'est lisse mais plus c'est lent.
- **Vitesse** (registre 6, valeur 0–9) : vitesse d'acquisition côté capteur. À combiner avec le filtre pour trouver le bon compromis bruit/réactivité — pour un tir court (< 2 s), privilégier la vitesse.

---

## Architecture du logiciel

```
banc_pousse_paul/
├── yr3180.py          ← driver bas niveau (Modbus RTU, thread-safe)
├── acquisition.py     ← worker QThread d'acquisition continue
├── analysis.py        ← fonctions pures d'analyse de tir (numpy)
├── gui.py             ← application PySide6 (point d'entrée)
├── config.json        ← persistance des réglages utilisateur (créé au runtime)
├── requirements.txt
└── (scripts CLI : Demo-TTL.py, Demo-read.py, test_all_commands.py, reset_config_yr3180.py)
```

### `yr3180.py` — driver Modbus RTU

Implémente la classe `YR3180` qui parle Modbus RTU directement avec `pyserial` (pas de dépendance à `pymodbus`). Garanties :

- **Thread-safe** : chaque transaction est protégée par un `threading.RLock`, on peut donc partager une instance entre l'acquisition et la GUI sans collision sur le port série.
- **Validation CRC** : le CRC-16 Modbus est recalculé sur chaque réponse ; en cas d'écart, `CRCError` est levée.
- **Retry** : 3 essais avec backoff sur erreur transitoire (CRC, timeout, exception Modbus).
- **Timeout exact** : `_read_exact()` boucle jusqu'à atteindre la longueur attendue ou expiration ; pas de trame tronquée silencieuse.

API principale :

```python
from yr3180 import YR3180

dev = YR3180(port="COM7", baudrate=9600)
dev.tare()
mass_kg = dev.read_weight_kg()        # poids signé en kg
dev.set_filter(1)                     # registre 5
dev.set_speed(5)                      # registre 6
dev.calibrate_lower()                 # zéro
dev.calibrate_upper()                 # full scale
dev.close()
```

### `acquisition.py` — worker QThread

`AcquisitionWorker(QThread)` lit le capteur en boucle et émet des signaux Qt :

| Signal | Charge utile | Émis quand |
|--------|--------------|-----------|
| `sample(t, force_n)` | timestamp relatif (s), force (N) | à chaque échantillon (~67 Hz) |
| `connection_lost(msg)` | message d'erreur | 5 erreurs Modbus consécutives |
| `status(msg)` | message texte | événements (tare, set_filter, etc.) |
| `rate(hz)` | fréquence mesurée | toutes les ~1 s |

Les commandes (tare, set_filter, set_speed, calibrate) passent par une `queue.Queue` interne pour rester thread-safe.

### `analysis.py` — fonctions pures

Aucune dépendance Qt → testable hors GUI. Fonctions clés :

- `peak_thrust(t, f)` → `(t_peak, f_peak)`
- `burn_window(t, f, threshold_n=2.0, min_duration_s=0.05, release_s=0.5)` → `(t_start, t_end)`
- `total_impulse(t, f, t_start, t_end)` → N·s (np.trapezoid)
- `average_thrust(t, f, t_start, t_end)` → N
- `specific_impulse(impulse_ns, propellant_mass_kg)` → s
- `summarize(t, f, ...)` / `format_report(summary)` pour le `.txt`

### `gui.py` — interface

Vue principale + dialogues. Le rendu du plot est limité à 30 fps via un `QTimer` pour rester fluide même si l'acquisition tourne plus vite. La GUI ne touche **jamais** directement au port série — toutes les actions passent par le worker.

---

## Câblage matériel

### Brochage YR-3180

| Pin YR-3180 | Fonction | Vers |
|-------------|----------|------|
| **E+**   | Alim cellule (+) | Cellule **5V OUT** |
| **E-**   | Masse cellule    | Cellule **GND**    |
| **INA+** | Signal cellule (+) | Cellule **INA+** |
| **INA-** | Signal cellule (–) | Cellule **INA-** |
| **5V**   | Alim module      | USB-TTL **5V**     |
| **RX**   | Réception        | USB-TTL **TX (orange)** |
| **TX**   | Émission         | USB-TTL **RX (jaune)**  |
| **GND**  | Masse            | USB-TTL **GND (noir)**  |
| **AL1**  | Sortie alarme 1  | (optionnel) |
| **AL2**  | Sortie alarme 2  | (optionnel) |

> ⚠️ Bien croiser RX/TX entre le YR-3180 et l'adaptateur USB-TTL.

![YR-3180 Synoptique](https://github.com/axpaul/YR-3180/blob/main/Image/YR-3180%20Synoptique.png)

### Boutons physiques du module

| Touche | Fonction |
|--------|----------|
| **Settings** | Naviguer / sauver les paramètres |
| **Shift**    | Basculer mode / tare |
| **Plus**     | Appui long → calibration full scale |
| **Minus**    | Appui long → calibration zéro |

---

## Calibration

Deux options : **par les boutons physiques** (procédure d'origine, ci-dessous) ou **depuis la GUI** (envoie les commandes Modbus équivalentes).

### Calibration zéro (méthode bouton)

1. Sans charge sur la cellule, appui long sur **Minus**.
2. Le module affiche `AD` (code ADC zéro). Attendre ~2 s, valider avec **Settings**.
3. Saisir le poids correspondant (0). Valider.
4. Affichage `END` → calibration zéro terminée.

### Calibration full scale (méthode bouton)

1. Poser un poids connu (≥ 20 % de la pleine échelle) sur la cellule.
2. Appui long sur **Plus**.
3. Le module affiche `AD` puis `PL`. Saisir le poids réel via Settings/Shift.
4. Affichage `END` → calibration terminée.

### Depuis la GUI

Le panneau « Contrôles » expose `calibrate_lower()` (zéro) et `calibrate_upper()` (full scale) qui écrivent dans le registre 32. Procéder dans le même ordre : zéro à vide d'abord, puis full scale avec poids connu.

---

## Référence YR-3180 (datasheet)

> Documentation traduite à partir de la datasheet officielle. Conservée ici pour référence rapide — la GUI n'a pas besoin de tous ces détails.

### Caractéristiques générales

| # | Symbole | Plage | Description | Défaut usine |
|---|---------|-------|-------------|--------------|
| 1 | LOCK | 0–99999 | Code d'accès aux paramètres généraux. Passer à 1231. | 1230 |
| 2 | dot  | 0.0 / 0.00 / 0.000 | Nombre de décimales (selon plage capteur 20 / 200 / 2000 kg) | 0.0 |
| 3 | LB   | 0–40 | Filtrage moyenne glissante. 0 = aucun ; 40 = très lissé mais lent. | 5 |
| 4 | Ad-H | 0 / 1 | Vitesse d'acquisition : 0 = lente, 1 = rapide | 0 |
| 5 | CLr  | 0–999.9 | Plage de tare automatique au démarrage | 5 |
| 6 | Fd   | 1, 2, 5, 10, 20, 50, 100, 200 | Graduation | 10 |
| 7 | ZEro | 0–9999 | Plage de zero tracking | 10 |
| 8 | Zt   | 10.0–600.0 | Temps de zero tracking (s) | 60.0 |
| 9 | PSET | 0.1000–9.9999 | Coefficient correctif sur la valeur affichée | 1.0000 |

### Alarmes

| # | Symbole | Plage | Description | Défaut |
|---|---------|-------|-------------|--------|
| – | LOCK | – | Passer à 1232 pour entrer dans le menu alarmes | 1230 |
| – | AL   | PVL / PVH / PVHL / OFF | Mode : PVL = AL1+AL2 sont des seuils bas ; PVH = les deux sont hauts ; PVHL = AL1 haut + AL2 bas ; OFF = désactivé | PVHL |
| 1 | AL1  | -1999.9 – 9999.9 | Seuil AL1 | 50.0 |
| 2 | AH1  | -1999.9 – 9999.9 | Hystérésis AL1 | 5.0 |
| 3 | AL2  | -1999.9 – 9999.9 | Seuil AL2 | 150.0 |
| 4 | AH2  | -1999.9 – 9999.9 | Hystérésis AL2 | 5.0 |

> ⚠️ Sortie AL1/AL2 en niveau bas quand alarme active.

### Communication

| # | Symbole | Plage | Description | Défaut |
|---|---------|-------|-------------|--------|
| – | LOCK | – | Passer à 1233 pour entrer dans le menu communication | 1230 |
| 1 | Addr | 001–255 | Adresse Modbus | 001 |
| 2 | Baud | 1200–115200 | Baudrate | 9600 |
| 3 | Pari | None / Odd / Even | Parité (toujours 8N1 par défaut) | None |
| 4 | Foalot | 1234 / 2134 / 3412 / 4321 | Ordre des octets pour les flottants | 1234 |

### Carte des registres

| Adresse | Nom |
|---------|-----|
| 0, 1   | Mesure (int32 signé, en mg) |
| 2, 3   | Mesure (float 32) |
| 4      | Décimales |
| 5      | Filtre |
| 6      | Vitesse d'acquisition |
| 7      | Graduation |
| 8      | Power-on clear |
| 9      | Auto clear |
| 10     | Délai auto clear |
| 11, 12 | Valeur de tare |
| 13, 14 | Facteur full scale |
| 15, 16 | Code ADC zéro |
| 17, 18 | Code ADC full scale |
| 19, 20 | Code filtré |
| 21, 22 | Code brut |
| 23, 24 | Limite basse de plage |
| 25, 26 | Limite haute de plage |
| 27     | Adresse Modbus |
| 28     | Baudrate |
| 29     | Parité |
| 30     | Ordre flottant |
| 32     | Calibration : 1 = zéro, 2 = full scale |
| 33     | Tare : 1 = appliquer, 2 = annuler |
| 48     | Mode alarme |
| 53, 54 | Seuil AL1 |
| 56, 57 | Seuil AL2 |
| 58, 59 | Hystérésis AL1 |
| 60, 61 | Hystérésis AL2 |
| 80     | Statut AL1 |
| 81     | Statut AL2 |

---

## Fichier CAO support

Un support imprimable 3D est fourni pour fixer le module sur le banc.

| Paramètre | Valeur |
|-----------|--------|
| Largeur totale | 54,5 mm |
| Hauteur | 34,0 mm |
| Largeur afficheur | 37,46 mm |
| Hauteur afficheur | 7,00 mm |
| Zone boutons | 31,5 mm |
| Espacement boutons | 10,3 mm |
| Hauteur PCB | 31,5 mm |

- **Fichier** : `CAO/Support YR3180 v°2 v9.stl`
- **Format** : STL
- **Fixation** : vis M3 ou bande adhésive
- **Orientation** : afficheur vers le haut, sortie câbles latérale

[Voir en 3D sur GitHub](https://github.com/axpaul/YR-3180/blob/main/CAO/Support%20YR3180%20v%C2%B02%20v9.stl)

![YR-3180 Size](https://github.com/axpaul/YR-3180/blob/main/Image/Size-YR-3180.png)

---

## Source

Documentation capteur extraite et traduite de la datasheet officielle YR-3180 : <https://www.yunzhan365.com/basic/83969503.html>
