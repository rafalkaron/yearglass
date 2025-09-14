import machine  # type: ignore

# MAX: 4294966
# 1 hour: 3600000 ms
# machine.deepsleep(3600000)
# machine.lightsleep(3600000)
print("before sleep")
machine.deepsleep(5000)
print("after sleep")
