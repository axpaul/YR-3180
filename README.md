# YR-3180 – Intelligent Weighing Digital Display Module

> 📄 This documentation is based on the official datasheet of the YR-3180 module and includes all available information and specifications.

---

## 1. Overview

![YR-3180 Front and Back View](https://github.com/axpaul/YR-3180/raw/main/Image/IMG_5954.JPEG)

The **weighing acquisition module** is a **high-performance**, **multi-functional** electronic weighing equipment.  
It adopts advanced **weighing sensor technology** and can measure the weight of items **in real time**, displaying the result with a **five-digit digital tube**.

It also includes **upper and lower limit alarm functions**, enabling **precise control and monitoring** of weight.  
At the same time, the product features a **TTL (5V) communication interface** and supports the **MODBUS RTU communication protocol**, allowing for fast and reliable communication with **PLCs**, **computers**, and other devices to enable **data transmission and remote control**.
Additionally, it supports **Type-C power supply** and includes **button-based debugging functions**, enhancing ease of use and operational stability.
Its main features include:

### Key Features

1. High-precision weighing sensor enables accurate weight detection and numerical display.  
2. Five-digit digital tube display, intuitive and clear, can achieve high-speed weighing and is suitable for efficient weighing process.  
3. Upper and lower limit alarm functions facilitate early warning and strict control to improve quality.  
4. Supports TTL communication interface and MODBUS RTU communication protocol to realize data transmission and remote control conveniently and quickly.  
5. Type-C /5V power supply and button debugging function, easy to use and strong stability.  
6. Light and portable, easy to install and move, saving space and cost. To sum up, the weighing acquisition module is a practical, high-performance, multi-functional electronic weighing equipment that can be widely used in weighing measurement and control applications in various production lines and logistics and warehousing situations to achieve weighing data Remote transmission and precise  

---

## 2. Size

![YR-3180 Size](https://github.com/axpaul/YR-3180/blob/main/Image/Size-YR-3180.png)

### Physical Dimensions

| Parameter         | Value   |
|------------------|---------|
| Total width       | 54.5 mm |
| Height            | 34.0 mm |
| Display width     | 37.46 mm |
| Display height    | 7.00 mm |
| Button zone       | 31.5 mm |
| Button spacing    | 10.3 mm |
| PCB height        | 31.5 mm |

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
- **5V**: Positive output of power  
- **RX**: Receive (other device’s TX)  
- **TX**: Transmit (other device’s RX)  
- **GND**: Negative power output

### Alarm interface
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
| 1  | `Lock` | 0–99999 | Press the SEL setting key, the display window will display the prompt LOCK, and then display 1230. Only after changing to 1231 can the following parameters be entered.| 1230 |
| 2  | `Dot` | 0.0 / 0.00 / 0.000 | 20kg sensor, can be set to 3 decimal points 20.000kg / 200kg sensor, can be set to 2 decimal points 200.00kg / 2000kg sensor, can be set to 1 decimal point 2000. Okg (based on sensor) | 0.0 |
| 3  | `LB` | 0–40 | 0-No processing, 1 to 40 times of sampling average filtering processing, the larger the setting value, the better the filtering effect, but the slower the speed will be. (higher = better filter, slower response) | 5 |
| 4  | `Ad-H` | 0 / 1 | Collection speed (0 = slow, 1 = fast) | 0 |
| 5  | `CLr` | 0–999.9 | The tare and tare range is cleared on power-on. When this parameter is greater than zero, the meter will automatically clear and tare within this range when it is powered on.n | 5 |
| 6  | `Fd` | 1–200 (steps) | Optional graduation values: 1, 2, 5, 10, 20, 50, 100, 200 | 1 |
| 7  | `Zero` | 0–9999 | Zero tracking range, automatically tracks. the deviation of weighing near the zero point, so that the gross weight display is maintained at the zero point. Note: Automatic clearing is invalid in automatic mode. | 10 |
| 8  | `Zt` | 10.0–600.0 | Zero tracking time, unit is seconds, factory default is 10 seconds. For example: after the weight value stabilizes, there will be no change in the value. After 10 seconds, it will be automatically cleared. After the value changes, restart the timer. | 60.0 |
| 9  | `PSET` | 1.0000–9.9999 | Correction coefficient, display value = display value X 1.0000 | 1.0000 |

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

