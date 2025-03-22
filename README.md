# YR-3180 – Intelligent Weighing Digital Display Module

---

> 📄 This documentation is based on the official datasheet of the YR-3180 module and includes all available information and specifications.

---

## Overview

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

![YR-3180 Front and Back View](https://github.com/axpaul/YR-3180/raw/main/Image/IMG_5954.JPEG)

---

## YR-3180 Weight Sensor – Serial Read Example

### Hardware Wiring

| YR-3180 Pin    | Function                  | Connects To                      |
|----------------|---------------------------|----------------------------------|
| **E+**         | Load cell power (+)       | Load cell **5V OUT**             |
| **E-**         | Load cell ground (–)      | Load cell **GND**                |
| **INA+**       | Load cell signal (+)      | Load cell **INA+**               |
| **INA-**       | Load cell signal (–)      | Load cell **INA-**               |
| **5V**         | Power input               | USB-TTL adapter **5V**           |
| **RX**         | Serial receive (input)    | USB-TTL **TX (orange)**          |
| **TX**         | Serial transmit (output)  | USB-TTL **RX (yellow)**          |
| **GND**        | Ground                    | USB-TTL **GND (black)**          |

> 💡 The USB-TTL adapter used is [TDI TTL-232R-5V-WE](https://ftdichip.com/products/ttl-232r-5v-we/) or any compatible 5V TTL adapter.  
> ⚠️ Be careful to cross RX and TX lines properly between the YR-3180 and the USB adapter.

![YR-3180 Synoptique](https://github.com/axpaul/YR-3180/blob/main/Image/YR-3180%20Synoptique.png)

---

### Python Script Overview

This Python script communicates with the **YR-3180** module using **Modbus RTU** over a serial (RS485/TTL) connection — without any external libraries like `pymodbus`, just using `pyserial`.

#### How it works:
1. A **Modbus RTU request frame** is manually built:
   - Slave address: `0x01`
   - Function code: `0x03` (Read Holding Registers)
   - Starting register: `0x0000`
   - Quantity: `2` registers
   - A CRC is calculated and appended

2. The request is sent over the serial port (e.g., `COM7` on Windows).

3. The response is parsed to extract **2 registers** (4 bytes).

4. These 4 bytes are combined into a **32-bit integer**, which is then converted into a weight value in **kilograms**.

---

## Size - Dimention

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

### CAD File

- **Filename**: `Support YR3180 v°2 v9.stl`
- **Format**: STL (compatible with most slicers and 3D printers)
- **Mounting**: Designed for M3 screws or adhesive tape (depending on use case)
- **Orientation**: Display facing up, cable access from the sides

---

## Wiring Diagram

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

## General Parameters

| Serial Number | Symbol | Predetermined Area | Illustrate | Factory Preset Value |
|---------------|--------|--------------------|------------|-----------------------|
| 1 | Lo ck | 0–99999 | Press the SEL setting key, the display window will display the prompt LOCK, and then display 1230. Only after changing to 1231 can the following parameters be entered. | 1230 |
| 2 | dot | 0.0<br>0.00<br>0.000 | 20kg sensor, can be set to 3 decimal points → 20.000kg<br>200kg sensor, can be set to 2 decimal points → 200.00kg<br>2000kg sensor, can be set to 1 decimal point → 2000.0kg | 0.0 |
| 3 | LB | 0–40 | 0 = No processing, 1 to 40 times of sampling average filtering processing. The larger the setting value, the better the filtering effect, but the slower the speed will be. | 5 |
| 4 | Ad-H | 0 / 1 | Collection speed: 0 = low speed, 1 = fast | 0 |
| 5 | CLr | 0–999.9 | The tare and tare range is cleared on power-on. When this parameter is greater than zero, the meter will automatically clear and tare within this range when it is powered on. | 5 |
| 6 | Fd | 1, 2, 5, 10, 20, 50, 100, 200 | Optional graduation values: 1, 2, 5, 10, 20, 50, 100, 200 | 10 |
| 7 | ZEro | 0–9999 | Zero tracking range, automatically tracks the deviation of weighing near the zero point, so that the gross weight display is maintained at the zero point.<br>Note: Automatic clearing is invalid in automatic mode. | 10 |
| 8 | Zt | 10.0–600.0 | Zero tracking time, unit is seconds, factory default is 10 seconds. For example: after the weight value stabilizes, there will be no change in the value. After 10 seconds, it will be automatically cleared. After the value changes, restart the timer. | 60.0 |
| 9 | PSET | 0.1000–9.9999 | Correction coefficient, display value = display value × 1.0000 | 1.0000 |

---

## Alarm Parameters

| Serial Number | Symbol | Predetermined Area | Illustrate | Factory Preset Value |
|---------------|--------|--------------------|------------|-----------------------|
| 01 | ikB | 0–9999 | Press the SEL setting key, the display window will display the prompt LOCK, and then display 1230. Only after changing to 1232 can the following parameters be entered. | 1230 |
|    | AL | PVL<br>PVH<br>PVHL<br>OFF | **PVL**: Both AL1 and AL2 are lower limit alarms. If the measured value is lower than the lower limit, the relay will close.<br>**PVH**: Both AL1 and AL2 are upper limit alarms. If the measured value is higher than the upper limit, the relay will close.<br>**PVHL**: AL1 is the upper limit alarm, AL2 is the lower limit alarm<br>**OFF**: Turn off the alarm function | PVHL |
| 1 | AL1 | -1999.9 – 9999.9 | AL1 upper limit alarm setting value. When the measured value exceeds (50.0), the relay operates. When the measured value is lower than 45.0, AL1 is disconnected. | 50.0 |
| 2 | AH1 | -1999.9 – 9999.9 | Upper limit alarm return difference value. | 5.0 |
| 3 | AL2 | -1999.9 – 9999.9 | AL2 upper limit alarm setting value. When the measured value exceeds (150.0), the relay operates. When the measured value is lower than 145.0, AL1 is disconnected. | 150.0 |
| 4 | AH2 | -1999.9 – 9999.9 | Upper limit alarm return difference value. | 5.0 |


### Individual Alarms

| # | Symbol | Range | Description | Default |
|---|--------|--------|-------------|---------|
| 1 | `AL1` | -1999.9–9999.9 | Upper limit threshold | 50.0 |
| 2 | `AH1` | -1999.9–9999.9 | Return difference for AL1 | 5.0 |
| 3 | `AL2` | -1999.9–9999.9 | Lower limit threshold | 150.0 |
| 4 | `AH2` | -1999.9–9999.9 | Return difference for AL2 | 5.0 |

---

## Communication Parameters

| Serial Number | Symbol | Predetermined Area | Illustrate | Factory Preset Value |
|---------------|--------|--------------------|------------|-----------------------|
| 01 | ikB | 0–9999 | Press the SEL setting key, the display window will display the prompt LOCK, and then display 1230. Only after changing to 1233 can the following parameters be entered. | 1230 |
| 02 | Addr | 001–255 | Modbus communication station number | 001 |
| 03 | Baud | 1200–115200 kbps | Communication port data transmission rate | 9600 |
| 04 | Pari | None | None: No check digit<br>Odd: even parity bit<br>Even: odd parity bit | 8,N,1 |
| 05 | Foalot | 1234<br>2134<br>3412<br>4321 | Data sequence:<br>12345678, 42CAFB10;<br>34127856, CA4201FB;<br>56781234, FB1042CA;<br>78563421, 10FBCA42. | 123 |

---

## Communication Register Address Map

### Communication Register Address

| Address   | Name                          |
|-----------|-------------------------------|
| 0, 1      | Measurements                  |
| 2, 3      | Floating point number         |
| 4         | Decimal point                 |
| 5         | Filter                        |
| 6         | Acquisition speed             |
| 7         | Graduation value              |
| 8         | Power-on clear value          |
| 9         | Automatically clear value     |
| 10        | Automatic clearing time       |
| 11, 12    | Tare value                    |
| 13, 14    | Full scale correction         |
| 15, 16    | Lower limit calibration AD    |
| 17, 18    | Upper limit calibration AD    |
| 19, 20    | Filter code acquisition       |
| 21, 22    | Original code                 |
| 23, 24    | Range lower limit value       |
| 25, 26    | Range upper limit             |
| 27        | Mailing address               |
| 28        | Baud rate                     |
| 29        | Check Digit                   |
| 30        | Floating point order          |
| 32        | Write 1 to calibrate the lower limit<br>Write 2 to calibrate the upper limit |
| 33        | Write 1 peel<br>Write 2 to cancel peeling |
| 48        | Alarm mode                    |
| 53, 54    | AL1 alarm value               |
| 58, 59    | AL1 return difference         |
| 56, 57    | AL2 alarm value               |
| 60, 61    | AL2 return difference         |
| 80        | AL1 alarm status              |
| 81        | AL2 alarm status              |


---

## Calibration Instructions

Press and hold the minus key, do not put weight on the sensor, press the setting key to change the value to 0.  
Press Set again and zero point calibration is completed.

### Press and hold the minus key to calibrate the zero point

| Step | Code | Description |
|------|------|-------------|
| 01 | AD | Zero-point AD acquisition code value, do not put weight on the sensor, wait for 2 seconds, press the setting button to save the zero-point acquisition code. |
| 02 | PL | Enter the weight value corresponding to the zero-point code value. There was no weight on the sensor just now, so the value is set to 0. |
| 03 | -END | Displaying `END` indicates that the calibration is completed and it will automatically return to the working state. |

---

Press and hold the plus button, put the weight on the sensor, press the setting button to change the value to the weight, press the setting button again, and the full scale calibration is completed.

### Long press the plus button to calibrate the full scale

| Step | Code | Description |
|------|------|-------------|
| 01 | AD | For the full-scale AD sampling value, a weight must be placed on the sensor. After waiting for 2 seconds, press the setting button to save the full-scale coding value. (More than 20% of sensor range) |
| 02 | PL | Enter the weight value corresponding to the full-scale code value. This value will be set to the weight just placed on the sensor. Press the Set button to save. |
| 03 | -END | Displaying `END` indicates that the calibration is completed and it will automatically return to the working state. |

---

## 📎 Source

All content provided is extracted and translated from the **official datasheet** of the YR-3180 Weighing Module, available on: [Datasheet](https://www.yunzhan365.com/basic/83969503.html)

