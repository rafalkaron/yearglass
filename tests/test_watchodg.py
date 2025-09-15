import machine  # type: ignore
import utime  # type: ignore

wdt = machine.WDT(timeout=5000)
utime.sleep(4999)
wdt.feed()
utime.sleep(5001)
wdt.feed()
