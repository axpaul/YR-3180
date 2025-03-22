# YR-3180 – Intelligent Weighing Digital Display Module

> 📄 This documentation is based on the official datasheet of the YR-3180 module and includes all available information and specifications.

---

## 1. Overview

The weighing acquisition module is a high-performance, multi-functional electronic weighing device. It adopts advanced sensor technology to measure the weight of items in real-time and displays the value on a **five-digit LED display**.

It also features upper and lower limit alarm functions for precise weight control and monitoring. The module supports **TTL and MODBUS RTU communication protocols**, making it compatible with PLCs, PCs, and other devices for remote data transmission and control.

Power is supplied via a **Type-C interface**, and configuration is facilitated by **button-based debugging**.

### Key Features

1. High-precision weighing sensor enables accurate weight detection and display.  
2. Five-digit digital display for intuitive and fast reading.  
3. Upper and lower limit alarms allow for early warnings and strict control.  
4. TTL and MODBUS RTU protocols for fast communication and control.  
5. Type-C power input and button-based debugging for stable and convenient use.  
6. Compact, lightweight, and easy to install.

---

## 2. Size


---

## 3. Wiring Diagram

### Power Supply
- **+5V**: Positive power supply  
- **GND**: Negative power supply

### Sensor Interface
- **E+**: Excitation positive (3.3V)  
- **E-**: Excitation negative (GND)  
- **S+**: Signal input positive  
- **S-**: Signal input negative

### Communication (TTL / MODBUS RTU)
- **SP+**: Positive output of power  
- **RX**: Receive (other device’s TX)  
- **TX**: Transmit (other device’s RX)  
- **GND**: Negative power output

### Alarm Outputs
- **AL1**: Upper limit alarm  
- **AL2**: Lower limit alarm  
→ Both are LOW level when alarming

### Operation Buttons
- **Settings**: Adjust and save parameters  
- **Shift**: Toggle mode / peel  
- **Plus key**: Long press to calibrate full scale  
- **Minus key**: Long press to calibrate zero

---

## 4. General Parameters

| #  | Symbol | Range | Description | Default |
|----|--------|-------|-------------|---------|
| 1  | `Lock` | 0–99999 | Access code (enter 1231 after LOCK prompt) | 1230 |
| 2  | `Dot` | 0.0 / 0.00 / 0.000 | Decimal precision (based on sensor) | 0.0 |
| 3  | `LB` | 0–40 | Averaging filter (higher = better filter, slower response) | 5 |
| 4  | `Ad-H` | 0 / 1 | Collection speed (0 = slow, 1 = fast) | 0 |
| 5  | `CLr` | 0–999.9 | Tare range cleared on power-on | 5 |
| 6  | `Fd` | 1–200 (steps) | Graduation value | 10 |
| 7  | `Zero` | 0–9999 | Auto-zero tracking range | 10 |
| 8  | `Zt` | 10.0–600.0 | Zero tracking time (sec) | 60.0 |
| 9  | `PSET` | 1.0000–9.9999 | Correction coefficient | 1.0000 |

---

## 5. Alarm Parameters

| #  | Symbol | Range | Description | Default |
|----|--------|--------|-------------|---------|
| 01 | `iAB`  | 0–9999 | Enter `1232` after LOCK prompt | 1230 |

### Alarm Mode Selection (`AL`)
- `PVL`: Both AL1 and AL2 are **lower limit alarms**  
- `PWH`: Both AL1 and AL2 are **upper limit alarms**  
- `PWL`: AL1 = upper limit, AL2 = lower limit  
- `OFF`: Disable alarms  
→ Default: `PVL`

### Individual Alarms

| # | Symbol | Range | Description | Default |
|---|--------|--------|-------------|---------|
| 1 | `AL1` | -1999.9–9999.9 | Upper limit threshold | 50.0 |
| 2 | `AH1` | -1999.9–9999.9 | Return difference for AL1 | 5.0 |
| 3 | `AL2` | -1999.9–9999.9 | Lower limit threshold | 150.0 |
| 4 | `AH2` | -1999.9–9999.9 | Return difference for AL2 | 5.0 |

---

## 6. Communication Parameters

| #  | Symbol | Range | Description | Default |
|----|--------|--------|-------------|---------|
| 01 | `iAB` | 0–9999 | Enter `1233` after LOCK prompt | 1230 |
| 02 | `Addr` | 001–255 | Modbus station address | 01 |
| 03 | `Baud` | 1200–115200 | Baud rate | 9600 |
| 04 | `Par` | None, Odd, Even | Parity setting | None |
| 05 | `Fomat` | 1234 / 3412 / 4321 | Data byte order | 123 |

---

## 7. Communication Register Address Map

| Address | Name | Description |
|---------|------|-------------|
| 0–1     | `Measurements` | Measurement value |
| 2–3     | `Floating point` | Decimal number |
| 4       | `Decimal point` | Display precision |
| 5       | `Filter` | Filter level |
| 6       | `Acquisition speed` | Sampling speed |
| 7       | `Graduation value` | Display step |
| 8       | `Power-on value` | Start value |
| 9       | `Auto clear` | Clear value on reset |
| 10      | `Auto clear enable` | 1 = enabled |
| 11–12   | `Tare value` | Tare data |
| 13–14   | `Full scale correction` | Calibration coefficient |
| 15–16   | `Lower limit AD` | AD value for AL2 |
| 17–18   | `Upper limit AD` | AD value for AL1 |
| 19–20   | `Filter code` | Internal filter setting |
| 21–22   | `Original code` | Factory code |
| 23–24   | `Range limit` | Full range |
| 25–26   | `Range upper limit` | Max scale |
| 32      | `Calibration trigger` | 1 = lower, 2 = upper |
| 33      | `Peeling` | Write 1 = peel |

---

## 8. Calibration Instructions

### ➖ Zero Point Calibration (Minus Key)
1. Do **not** apply any weight  
2. Hold `Minus`, press `SET`, wait for value `0`  
3. Release when `END` appears = completed

| Step | Code | Action |
|------|------|--------|
| 01 | `AD` | Capture zero-point AD (no weight) |
| 02 | `PL` | Input corresponding weight (0) |
| 03 | `END` | Confirmation message |

---

### ➕ Full Scale Calibration (Plus Key)
1. Apply known weight  
2. Hold `Plus`, press `SET`, wait for confirmation  
3. Release when `END` appears = completed

| Step | Code | Action |
|------|------|--------|
| 01 | `AD` | Capture full-scale AD (with load) |
| 02 | `PL` | Input known weight |
| 03 | `END` | Confirmation message |

---

## 📎 Source

All content provided is extracted and translated from the **official datasheet** of the YR-3180 Weighing Module, available on:  
👉 [https://www.yunzhan365.com/basic/83969503.html](https://www.yunzhan365.com/basic/83969503.html)

