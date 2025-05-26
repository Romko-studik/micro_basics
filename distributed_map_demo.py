#!/usr/bin/env python3

import hazelcast


hz_client = hazelcast.HazelcastClient()
counter_map = hz_client.get_map("distributed-map")


for i in range(1000):
    counter_map.set(f"{i}", i).result()

print("Counter map size:", counter_map.size().result())
hz_client.shutdown()
