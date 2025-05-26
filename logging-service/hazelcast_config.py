import hazelcast
import logging

import hazelcast.config

logger = logging.getLogger(__name__)

class HazelcastManager:
    def __init__(self, cluster_name="logging-cluster", instance_name=None):
        self.cluster_name = cluster_name
        self.instance_name = instance_name or f"logging-service-{id(self)}"
        self.client = None
        self.messages_map = None
        
    def connect(self):
        """Initialize Hazelcast client"""
        try:
            hz_client = hazelcast.HazelcastClient()            
            self.messages_map = hz_client.get_map("distributed-map")
            logger.info(f"Hazelcast client connected: {self.instance_name}")
            logger.info(f"Using map: {self.messages_map.name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Hazelcast: {e}")
            self.messages_map = {}
            logger.warning("Using in-memory storage as fallback")
    
    def disconnect(self):
        if self.client:
            self.client.shutdown()
            logger.info("Hazelcast client disconnected")
    
    def put_message(self, key: str, message: str):
        try:
            if hasattr(self.messages_map, 'put'):
                self.messages_map.put(key, message)
            else:
                self.messages_map[key] = message
            logger.info(f"Stored message: {key} = {message}")
        except Exception as e:
            logger.error(f"Error storing message: {e}")
    
    def get_message(self, key: str) -> str:
        try:
            if hasattr(self.messages_map, 'get'):
                return self.messages_map.get(key)
            else:
                return self.messages_map.get(key)
        except Exception as e:
            logger.error(f"Error retrieving message: {e}")
            return None
    
    def get_all_messages(self) -> dict:
        try:
            if hasattr(self.messages_map, 'entry_set'):
                return dict(self.messages_map.entry_set())
            else:
                return dict(self.messages_map)
        except Exception as e:
            logger.error(f"Error retrieving all messages: {e}")
            return {}
    
    def get_map_size(self) -> int:
        try:
            if hasattr(self.messages_map, 'size'):
                return self.messages_map.size()
            else:
                return len(self.messages_map)
        except Exception as e:
            logger.error(f"Error getting map size: {e}")
            return 0