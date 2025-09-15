import machine  # type: ignore


def usb_powered() -> bool:
    """Check if Pico is powered from USB."""
    vbus = machine.Pin("WL_GPIO2", machine.Pin.IN)
    return vbus.value() == 1


def usbprint(*args, **kwargs) -> None:
    """
    Print to console only if USB power (VBUS) is present.
    Accepts same arguments as built-in print().
    """
    if usb_powered():
        print(*args, **kwargs)
