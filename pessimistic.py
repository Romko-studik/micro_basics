#!/usr/bin/env python3

import hazelcast

hz_client = hazelcast.HazelcastClient()
counter_map = hz_client.get_map("distributed-map").blocking()

counter_map.put_if_absent("key-2", 0)

for i in range(10000):
    counter_map.lock("key-2")
    try:
        current_value = counter_map.get("key-2")
        updated_value = current_value + 1
        counter_map.put("key-2", updated_value)
    finally:
        counter_map.unlock("key-2")

print("Counter map size:", counter_map.size())
print("Final value for key-2:", counter_map.get("key-2"))

hz_client.shutdown()
