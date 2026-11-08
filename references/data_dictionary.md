# WaferPulse Sensor Telemetry Data Dictionary

## 1. Primary Identification & Quality Target

| Field | Data Type | Value Domain | Description |
| :--- | :--- | :--- | :--- |
| `Wafer` | String | `Wafer_YYYYMMDD_HHMMSS_idx` | Unique manufacturing lot and wafer barcode tracking key |
| `Output` | Integer | `1` (Good), `-1` (Defective) | Fab inline quality gate inspection result |

---

## 2. Sensor Telemetry Channels (`Sensor_1` to `Sensor_60`)

The wafer fabrication line features 60 real-time telemetry sensors streaming from Chemical Mechanical Planarization (CMP), EUV Photolithography, and Reactive Ion Plasma Etching chambers:

| Sensor Group | Channels | Unit | Physical Parameter | Nominal Range |
| :--- | :--- | :--- | :--- | :--- |
| **RF Generator & Plasma Bias** | `Sensor_1` - `Sensor_15` | kW, V | Forward RF power, reflected power, DC bias | 13.0 - 14.5 kW |
| **Chamber Pressure & Vacuum** | `Sensor_16` - `Sensor_28` | mTorr | Process chamber vacuum, turbo pump throttle | 14.0 - 16.5 mTorr |
| **Thermal & Chuck Control** | `Sensor_29` - `Sensor_40` | °C | Electrostatic chuck surface temp, coolant delta | 62.0 - 68.0 °C |
| **Gas Mass Flow Controllers** | `Sensor_41` - `Sensor_50` | sccm | $CF_4$, $O_2$, $Ar$ plasma etching chemistry flow | 220 - 260 sccm |
| **Backside Helium Cooling** | `Sensor_51` - `Sensor_60` | Torr | Wafer backside heat transfer pressure | 8.0 - 12.0 Torr |

---

## 3. Physical Chamber Regimes (Clustering)

- **Chamber A (CMP Polishing)**: Baseline reference chamber with standard slurry flow and pad conditioning.
- **Chamber B (Photolithography)**: Narrow-tolerance optical alignment with strict thermal control.
- **Chamber C (Plasma Etching)**: High-energy RF plasma regime sensitive to polymer deposition and electrode wear.

---

## 4. Anomaly Thresholds & Drift Bounds

- **Z-Score Anomaly Severity**:
  - $|Z| < 2.0$: Nominal operating window
  - $2.0 \le |Z| < 3.0$: Warning (tool calibration advisory)
  - $|Z| \ge 3.0$: Critical deviation (fault injected / defective wafer)
- **Population Stability Index (PSI)**:
  - $PSI < 0.10$: Stable distribution
  - $0.10 \le PSI < 0.25$: Moderate drift (scheduled maintenance recommended)
  - $PSI \ge 0.25$: Critical drift (retraining required)
