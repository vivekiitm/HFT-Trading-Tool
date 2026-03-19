import core
import random
import time

engine = core.MatchingEngine()

start = time.time()

for _ in range(1_000_000):
    price = random.randint(100000, 101000)
    engine.process_order(True, price, 1)

end = time.time()

print("Throughput:", 1_000_000 / (end - start), "orders/sec")
print("Microprice:", core.microprice(engine))
