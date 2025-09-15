import machine  # type: ignore

# MAX: 4294966
# 1 hour: 3600000 ms
print("before sleep")
machine.deepsleep(5000)
print("after sleep")
