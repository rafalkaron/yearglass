# Yearglass

Use Yearglass to display interesting data on your desk.

## Operation

### Using Yearglass

Display different information on Yearglass.

* To change the display mode, do any of the following:

    | Button            | Action                          |
    |-------------------|---------------------------------|
    | Top-left button   | Display current year's progress |
    | Middle-left button| Display some art                |
    | Bottom-left button| Display a quote                 |

* To refresh or display a new item, press the same mode button again.

## Development

Build your own Yearglass!

### Components

Yearglass uses low-power components to ensure long operation on a single charge.

| Component         | Quantity | Description                                 |
|-------------------|----------|---------------------------------------------|
| Controller        | 1        | Raspberry Pi Pico W                         |
| Display           | 1        | Waveshare Pico-ePaper-2.7 (264x176 Pixels)  |
| Battery           | 3        | AA NiMH rechargeable batteries (1.2V each)  |
| Battery pack      | 1        | For 3 AA batteries                          |
| Wires             | 2        | For connecting to power                     |
| Chassis/board     | 1        | Components for keeping Yearglass together   |

### Software

Yearglass is coded with power-efficiency in mind.

1. Flash the latest MicroPython onto the Raspberry Pi Pico W(H).
2. Upload the necessary files from this repository to Raspberry Pi Pico W(H).

### Wiring

| Pico W GPIO Pin | Connects to               | Description                      |
|-----------------|---------------------------|----------------------------------|
| VSYS            | VCC (Display)             | Power input                      |
| GND             | GND (Display)             | Ground                           |
| GP11            | DIN (MOSI, Display)       | MOSI pin of SPI interface        |
| GP10            | CLK (SCK, Display)        | SCK pin of SPI interface         |
| GP9             | CS (Display)              | Chip select pin, Low Active      |
| GP8             | DC (Display)              | Data/Command control             |
| GP12            | RST (Display)             | Reset pin, low active            |
| GP13            | BUSY (Display)            | Busy output pin                  |
| GP15            | KEY1 (Top-left Button)    | Button 1 input                   |
| GP17            | KEY2 (Middle-left Button) | Button 2 input                   |
| GP2             | KEY3 (Bottom-left Button) | Button 3 input                   |
