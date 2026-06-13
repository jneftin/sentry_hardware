# Validated BOM - Warehouse Intelligence (UNO Q) - 2026-06-12

Canonical orderable parts list. Validated against vendor docs, Arduino forum, and
Edge Impulse via deep research on 2026-06-12. Supersedes the parts table in the
Obsidian vault note "02 Bill of Materials" (that note now points here).

## Already owned
- 1x Arduino UNO Q 4GB - 32GB eMMC, Qualcomm Dragonwing QRB2210 (quad A53) + STM32U585.

## Order now - hub
| Item | Qty | Note |
|---|---|---|
| Arduino USB-C Hub 8-in-1 (TPX00241) | 1 | OFFICIAL, Arduino-tested. 65W PD passthrough + HDMI + Ethernet + USB-A 2.0 + SD/TF. Replaces the generic Anker pick. Ethernet lets the hub skip warehouse WiFi. |
| Arduino 45W USB-C PSU (or 45W+ PD charger owned) | 1 | Powers board + hub + camera with margin. |
| Logitech C920 | 1 | Confirmed working on UNO Q. Buy ONE - two-stream FPS is unverified. |
| Heatsink + fan (RPi kit) | 1 | Dragonwing throttles under sustained inference. |

## Order now - satellites
| Item | Qty | Note |
|---|---|---|
| Genuine XIAO ESP32-S3 Sense | 3 | Must include camera+mic expansion board, 8MB PSRAM / 8MB flash. NOTE: new Sense ships OV3660 (OV2640 discontinued) - confirm Edge Impulse camera support. 1 unit is a spare. |
| ESP32-C3 (3-pack) | 1 | Spare included. |
| BME280 (confirm humidity, NOT BMP280) | 2 | |
| LIS3DH accelerometer | 2 | |

## Order now - STM32 honest job + bench/field extras
| Item | Qty | Note |
|---|---|---|
| AM312 mini PIR | 1 | 3.3V supply, 3.3V output - wires straight to STM32 GPIO, no level shifter. Use INSTEAD of HC-SR501 (5V / level-shift risk). Verify output level on datasheet. |
| Small relay module or LED/buzzer | 1 | The STM32 output half of the honest job. |
| Multi-port USB charger + cables | 1 set | Powers the 4 satellite nodes. |
| Magnetic accel mount | 1-2 | Couples LIS3DH to the machine, not a shelf. Otherwise it reads floor vibration. |
| Breadboard + jumpers + USB DATA cables + phone tripod clamp | - | Confirm cables are DATA, not charge-only. |

Approx total: ~$260-290 (hub/PSU price confirm at checkout).

## Node role assignment (no quantity change from the original plan)
- Hub: 1x C920 -> YOLOv8n person/forklift, homography heatmap (the App Lab showpiece).
- XIAO #1 -> FOMO person counting (on-MCU vision).
- XIAO #2 -> acoustic anomaly (onboard mic, EI audio, score-only publish). HERO feature.
- XIAO #3 -> spare.
- ESP32-C3 #1 and #2 -> each carries BME280 + LIS3DH (environment + vibration).

## Corrections from deep research (what the earlier plan got wrong)
1. POWER. UNO Q is NOT single-USB-C-only. It has USB-C PD (5V/3A=15W, SINK ONLY) AND a
   7-24V VIN input. USB-C cannot power downstream devices, so a POWERED hub is required.
   Path A (recommended): official 45W PSU -> official 8-in-1 hub -> board + C920.
   Path B (robust for fixed install): 12V into VIN, plain powered hub on USB-C for peripherals.
   Path C (cheapest, 1 camera): ~$13 USB-C PD+USB3 OTG adapter (one roadtester booted a webcam with it).
2. STORAGE. 32GB eMMC, ample for OS + Mosquitto + Python + OpenCV + YOLOv8n NCNN + a week of
   per-minute SQLite. No confirmed microSD slot on the board - do not rely on one (hub has SD reader).
3. ACOUSTIC. Onboard mic = 16kHz sampling -> ~8kHz usable band. Legitimate "audible anomaly" V1.
   NOT honest as "early bearing-fault detection" (those are ultrasonic >20kHz). Scope the claim.
   V2 upgrade: ultrasonic MEMS mic (SPH0641LU) + ADXL1002 accelerometer.
4. CAMERA OPTION. Official UNO Media Carrier adds 2x MIPI CSI ports (Raspberry Pi cameras) for
   serious dual-camera vision. C920 stays the pragmatic pilot pick; Media Carrier is the upgrade
   path if 2-camera vision becomes core.

## Must bench-test before trusting (no datasheet settles these)
- Real YOLOv8n NCNN FPS on the UNO Q. THE binding vision-tier unknown. Do not promise 2 streams until measured.
- UNO Q boots through the hub with C920 attached; lsusb sees the camera after a cold reboot, not just hot-plug.
- 8h+ sustained capture: no thermal throttle, no disk fill, no leak.
- XIAO mic noise floor next to real equipment; OV3660 works with the EI FOMO camera export.
- AM312 output confirmed 3.3V before wiring to STM32 GPIO.

## Sourcing
- Build now = Amazon / Arduino store (Prime, lands this week). Time at $90-165/hr beats saving $50.
- Produce later = AliExpress only at fleet volume (20+ generic nodes).
