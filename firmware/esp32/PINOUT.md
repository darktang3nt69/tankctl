---
title: PINOUT
type: note
permalink: tankctl/firmware/esp32/pinout
---

# ESP32 WROOM 32D Pinout Reference

## Physical Pin Layout (Top View)

```
     USB
      |
  [GND] [GND] [GND]
  [3V3] [EN ]
  [36 ] [SVP] ← ADC (don't use for GPIO)
  [39 ] [SVN] ← ADC (don't use for GPIO)
  [34 ] [IO35] ← ADC
  [IO32] [IO33]
  [IO25] [IO26]
  [IO27] [IO14]
  [IO13] [IO12]
  [IO9 ] [IO11]
  [IO10] [ IO8]
  [IO7 ] [ IO6]
  [IO5 ] [ IO18] ← SPI CLK
  [IO17] [ IO16]
  [IO4 ] ← ⭐ RELAY (configured in firmware)
  [IO0 ] [ IO2 ] ← STATUS LED (optional)
  [IO15] [ IO13]
  [GND] [3V3]
  [GND] [EN ]
```

## TankCtl Configuration

| Function | GPIO | Notes |
|----------|------|-------|
| **Relay Control** | 4 | Active-LOW (HIGH=OFF, LOW=ON) |
| **Temperature** | 23 | 1-Wire protocol, needs 4.7kΩ pullup |
| **Status LED** | 2 | Optional; pulse/blink for connection status |

## Complete ESP32 Pinout

### Input-Only Pins (don't use as output!)
- GPIO 34, 35, 36, 39 (Analog input only)
- GPIO 6, 7, 8, 9, 10, 11 (Flash memory, reserved)

### Good GPIO for IoT (safe to use)
✅ GPIO 0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33

### Special Functions
- **GPIO 0** - Boot mode select (pulled up, can use with care)
- **GPIO 2** - On-board LED (some boards)
- **GPIO 5** - SPI CLK
- **GPIO 12-15** - SPI data lines (if using SPI)
- **GPIO 16, 17** - UART 2 (if using serial)

## Wiring Diagram

### Relay Module
```
ESP32 GPIO 4  →  Relay IN
ESP32 GND     →  Relay GND
ESP32 3V3     →  Relay VCC (5V relay with buck converter)
```

### Temperature Sensor (DS18B20)
```
ESP32 3V3 ─[4.7kΩ]─┬─ GPIO 23 (data)
                    │
DS18B20 Pin 1 (GND) ─┤
DS18B20 Pin 2 (data)┤
DS18B20 Pin 3 (3V3) ┴─ ESP32 3V3
```

### Status LED (optional)
```
ESP32 GPIO 2 ─[220Ω]─ LED ─ GND
                    ↑       ↑
              anode        cathode
```

## Default I2C / SPI Pins

### I2C (if used)
- SDA: GPIO 21
- SCL: GPIO 22

### SPI (if used)
- MOSI: GPIO 23 ⚠️ (conflicts with temperature sensor!)
- MISO: GPIO 19
- CLK: GPIO 18
- CS: GPIO 5

## Power Pins

- **3.3V** - Regulated power output (can source ~1A)
- **GND** - Ground (multiple available)
- **5V** - USB power (when connected, not available as output)
- **EN** - Enable pin (pull LOW to reset)

## Additional Components Needed

### External Relay (optional amplifier)
```
┌─────────────────┐
│  Relay Module   │
├─────────────────┤
│ IN   →  GPIO 4  │
│ GND  →  GND     │
│ VCC  →  5V*     │
│ COM  →  AP +12V │
│ NO   →  Pump    │
│ NC   →  [unused]│
└─────────────────┘
* Use 5V buck converter if only 3.3V available
```

### Buck Converter (5V relay on 3.3V logic)
```
ESP32 5V (USB) ──[ Buck ]── 5V out → Relay VCC
ESP32 GND ────────[ Buck ]── GND out → Relay GND
```

## Recommended Carrier Board Connections

If using a development board with headers:

```
Relay      → PIN labeled "4" or "GPIO4"
Temp       → PIN labeled "23" or "GPIO23"
Status LED → PIN labeled "2" or "GPIO2"
GND        → Any PIN labeled "GND"
3.3V       → Any PIN labeled "3V3"
```

## SPI Conflict Resolution

⚠️ If you need SPI **AND** OneWire temperature:
- Keep temp on GPIO 23 (OneWire only)
- Use SPI on GPIO 18, 19, 5 (MOSI/MISO/CLK)
- Choose independent CS pin (not conflicting)

## Power Distribution Recommendation

```
                 ┌── ESP32 3.3V → Temperature sensor VCC
                 │               → 4.7kΩ pullup (to GPIO 23)
Power Supply ────┤
                 │
                 └── 5V Relay → Relay IN (via GPIO 4)
```

## Troubleshooting: Pin Not Responding

| Symptom | Cause | Fix |
|---------|-------|-----|
| GPIO 4 stays HIGH | Relay logic inverted | Check `digitalWrite()` logic |
| GPIO 23 no signal | Sensor wiring | Verify 4.7kΩ pullup across |
| LED always ON | Wrong GPIO | Check STATUS_LED_PIN define |
| Upload fails | Boot pin pulled | Press BOOT during upload |
| ESP32 won't boot | GND not connected | Check all GND pins |

## Safety Tips

1. **ESP32 is 3.3V logic** - Do NOT connect 5V directly!
2. **Relay needs external power** - Don't power from ESP32 alone
3. **Thermal**: Keep ESP32 cool (can reach 80°C under WiFi load)
4. **ESD**: Use grounding strap when handling
5. **Overcurrent**: Add polyfuse on 3.3V output (from external supply)

## For Mass Production

If deploying multiple units:
- Use same GPIO assignments (consistency)
- Pre-program tank IDs in firmware or via serial
- Test all GPIOs before deployment
- Use industrial-grade temperature sensors (not bread-board friendly)

## Reference

- ESP32 Datasheet: https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf
- GPIO Matrix: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/gpio.html