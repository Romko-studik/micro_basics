#!/usr/bin/env python3
import hazelcast
import threading
import time

hz_client = hazelcast.HazelcastClient()

hz_queue = hz_client.get_queue("bounded-queue")
while hz_queue.size().result() > 0:
    item = hz_queue.poll(5).result()
    if item is not None:
        print(f"Clearing item: {item}")
    else:
        print("Queue is empty, nothing to clear.")

def add_items():
    for i in range(100):
        hz_queue.offer(i,5).result()
    hz_queue.offer("STOP", 5).result()  # Signal to stop reading

def read_items(reader_id = 0):
    for _ in range (100):
        res = hz_queue.take().result()
        if res == "STOP":
            print(f"Reader {reader_id} received stop signal.")
            hz_queue.offer("STOP", 5).result()
            return
        print(f"Reader {reader_id} received item: {res}")
adder_thread = threading.Thread(target=add_items)
reader_thread_1 = threading.Thread(target=read_items, args=(1,))
reader_thread_2 = threading.Thread(target=read_items, args=(2,))

reader_thread_1.start()
reader_thread_2.start()
adder_thread.start()


reader_thread_1.join()
reader_thread_2.join()
adder_thread.join()
print("Final queue size:", hz_queue.size().result())
hz_client.shutdown()

