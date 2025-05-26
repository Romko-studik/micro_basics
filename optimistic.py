#!/usr/bin/env python3

import hazelcast

hz_client = hazelcast.HazelcastClient()
counter_map = hz_client.get_map("distributed-map").blocking()

counter_map.put_if_absent("key-3", 0)

for i in range(10000):
    current_value = counter_map.get("key-3")
    counter_map.replace_if_same("key-3", current_value, current_value + 1)    

print("Counter map size:", counter_map.size())
print("Final value for key-3:", counter_map.get("key-3"))
hz_client.shutdown()
