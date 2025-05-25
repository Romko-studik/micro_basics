import hazelcast
import time
import threading

def connect_client():
    """Connect to Hazelcast cluster"""
    client = hazelcast.HazelcastClient(
        cluster_members=["127.0.0.1:5701", "127.0.0.1:5702", "127.0.0.1:5703"],
        cluster_name="lab-cluster"
    )
    return client

def populate_map():
    """Populate distributed map with 1000 values"""
    client = connect_client()
    distributed_map = client.get_map("capitals").blocking()
    
    print("Populating map with 1000 entries...")
    start_time = time.time()
    
    for i in range(1000):
        distributed_map.put(str(i), f"value_{i}")
        if i % 100 == 0:
            print(f"Added {i} entries...")
    
    end_time = time.time()
    print(f"Map populated with {distributed_map.size()} entries in {end_time - start_time:.2f} seconds")
    
    client.shutdown()

if __name__ == "__main__":
    populate_map()