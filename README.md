# Yearglass

Display year progress in unusual ways on an epaper display.

## Using Yearglass

Turn Yearglass on and switch between different modes of year progress visualization.

1. Turn Yearglass on.  
    **Result:** Yearglass initializes and the internal LED turns on. Once completed, the internal LED turns off and the default mode displays.
2. To change the display mode, use the buttons as follows:

    | Button        | Action                        |
    |---------------|-------------------------------|
    | Right button  | Display next visualization    |
    | Left button   | Display previous visualization|
    | Middle button | Display random visualization  |

### Display modes reference

Yearglass includes the following visualization modes:

| Mode       | Description                                             |
|------------|---------------------------------------------------------|
| Hourglass  | Displays year progress in the shape of an hourglass     |
| Level      | Displays year progress as a vertical level bar          |
| Pie Chart  | Displays year progress as a rectangular pie chart       |
| Spiral     | Displays year progress as a snake-like visualization    |
| Crossout   | Displays remaining days as `.` and elapsed days as `x`  |

### Status reference

Yearglass internal LED indicates the following:

| LED Status                | Description                                   |
|---------------------------|-----------------------------------------------|
| Off                       | Idle or powered down                          |
| On                        | Busy with getting or displaying data          |
| Blinking every 0.5s       | Problem in the main loop                      |
| Blinking every 1s         | Problem with updating data                    |
| Blinking every 2s         | Problem with displaying data                  |
| Blinking every 3s         | Problem with optional hardware initialization |

**NOTE:** In case of hangs, freezes, or infinite loops, Yearglass automatically resets after 25 hours.

## Development

Build your own Yearglass!

### Software

Yearglass is coded with power-efficiency in mind.

1. Flash the latest MicroPython onto the Raspberry Pi Pico W(H).
2. (optional) To obtain time from WiFi, create a `config.py` file in the root directory of the project:  

    ```python
    WIFI_SSID = "WiFiNetworkName"
    WIFI_PASSWORD = "WiFiPassword"
    ```
3. Upload the necessary files from this repository to Raspberry Pi Pico W(H).

### Components reference

Yearglass uses low-power components to ensure long operation on a single charge.

| Component         | Quantity | Description                                                                    |
|-------------------|----------|--------------------------------------------------------------------------------|
| Controller        | 1        | Raspberry Pi Pico W(H)                                                         |
| Display           | 1        | Waveshare Pico-ePaper-2.7 (264x176 Pixels)                                     |
| RTC module        | 1        | RTC PCF8563 I2C - Waveshare 3707                                               |
| Battery           | 3        | AA NiMH rechargeable batteries (1.2V each, connected in series for 3.6V total) |
| Battery pack      | 1        | For 3 AA batteries                                                             |
| Wires             | several  | For connecting components                                                      |
| Chassis           | 1        | Components for keeping Yearglass together                                      |

### Wiring reference

| Pico W Pin      | Connects to                      | Description                              |
|-----------------|----------------------------------|------------------------------------------|
| VSYS            | VCC (Display, RTC)               | Power input (3.3V/5V as required)        |
| GND             | GND (Display, RTC)               | Ground                                   |
| GP11            | DIN (MOSI, Display)              | MOSI pin of SPI interface (Display)      |
| GP10            | CLK (SCK, Display)               | SCK pin of SPI interface (Display)       |
| GP9             | CS (Display)                     | Chip select pin, Low Active (Display)    |
| GP8             | DC (Display)                     | Data/Command control (Display)           |
| GP12            | RST (Display)                    | Reset pin, low active (Display)          |
| GP13            | BUSY (Display)                   | Busy output pin (Display)                |
| GP15            | KEY1 (Top-left Button)           | Button 1 input                           |
| GP17            | KEY2 (Middle-left Button)        | Button 2 input                           |
| GP2             | KEY3 (Bottom-left Button)        | Button 3 input                           |
| GP4             | SDA (RTC)                        | I2C SDA for RTC PCF8563                  |
| GP5             | SCL (RTC)                        | I2C SCL for RTC PCF8563                  |
