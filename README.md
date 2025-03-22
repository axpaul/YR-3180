# YR-3180 – Intelligent Weighing Digital Display

## 1. Overview

The weighing acquisition module is a high-performance, multi-functional electronic weighing equipment. It adopts advanced weighing sensing technology and can measure the weight of items in real time, displaying it with a five-digit digital tube.

It also includes upper and lower limit alarm functions, allowing precise weighing control and monitoring. Additionally, this product supports a TTL communication interface and MODBUS RTU communication protocol, enabling convenient and rapid communication with PLCs, computers, and other equipment for data transmission and remote control.

It supports Type-C power supply and button-based debugging functions for enhanced convenience and stability.

### Main Features

- **High-precision sensor** for accurate weight detection and numerical display  
- **Five-digit digital display**, intuitive and clear  
- **Upper and lower limit alarms** for early warnings and strict control  
- **TTL and MODBUS RTU** support for fast communication and control  
- **Type-C power supply** and **debug button** for easy use and stability  
- **Lightweight and portable**, easy to install and space-saving

### Conclusion

In summary, this weighing module is a practical, high-performance, multi-functional solution suitable for weighing and control applications in production lines, logistics, and warehousing. It enables remote data transmission and precise monitoring.

---

## 4. General Parameters and Communication Settings

| No. | Symbol | Range | Description | Default |
|-----|--------|--------|-------------|---------|
| 1 | `Lock` | 0–99999 | Press SEL → displays `LOCK`, then `1230`. Set to `1231` to access config. | 1230 |
| 2 | `Dot` | 0.0 / 0.00 / 0.000 | Decimal precision (depends on sensor capacity) | 0.0 |
| 3 | `LB` | 0–40 | Sampling average filter (0 = no filtering) | 5 |
| 4 | `Ad-H` | 0–1 | Data acquisition speed: 0 = low, 1 = fast | 1 |
| 5 | `CLr` | 0–999.9 | Clears tare on power-up | 5 |
| 6 | `Fd` | 1, 2, 5, 10, 20, 50, 100, 200 | Graduation values | 10 |
| 7 | `Zt` | 10.0–600.0 | Zero tracking time (seconds) | 60.0 |
| 8 | `PSET` | 0.1000–9.9999 | Correction coefficient | 1.0000 |

---

## 6. Communication Parameters

| No. | Symbol | Range | Description | Default |
|-----|--------|--------|-------------|---------|
| 01 | `iAB` | 0–9999 | Press SEL → `LOCK` → enter `1232` to access | 1230 |
| 02 | `Addr` | 001–255 | Modbus station number | 01 |
| 03 | `Baud` | 1200–115200 | Baud rate for data transmission | 9600 |
| 04 | `Par` | None, Odd, Even | Parity check | None |
| 05 | `F01` | 1234 | Data sequence | 123 |

---

## 7. Communication Register Address Table

| Address | Name | Description |
|---------|------|-------------|
| 0, 1 | `Measurements` | Measurement values |
| 2, 3 | `Floating Point` | Decimal format |
| 5 | `Filter` | Filtering configuration |
| 6 | `Acquisition Speed` | Data collection rate |
| 9 | `Auto Clear` | Automatically clears value on reset |
| 15, 16 | `Lower Limit Cal.` | AD calibration for lower limit |
| 17, 18 | `Upper Limit Cal.` | AD calibration for upper limit |
| 21, 22 | `Original Code` | Initial code setup |
| 25, 26 | `Upper Limit` | Range upper limit |
| 32 | `Calibration Mode` | Write `1` = lower limit, `2` = upper limit |

---

