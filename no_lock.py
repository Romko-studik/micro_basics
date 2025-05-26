#!/usr/bin/env python3

import hazelcast

hz_client = hazelcast.HazelcastClient()
counter_map = hz_client.get_map("distributed-map")
counter_map.put_if_absent("key-1", 0).result()

for i in range(10000):
    current_value: int = counter_map.get("key-1").result()
    updated_value = current_value + 1
    counter_map.put("key-1", updated_value)

print("Counter map size:", counter_map.size().result())
print("Final value for key-1:", counter_map.get("key-1").result())
hz_client.shutdown()
