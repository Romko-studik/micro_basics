import hazelcast
import logging
import consul
logger = logging.getLogger(__name__)

def create_hazelcast_client() -> hazelcast.HazelcastClient:
    # read cluster config from Consul
    cluster = read_kv("hazelcast/cluster_name")
    members = read_kv("hazelcast/members").split(",")
    logger.info(f"Connecting Hazelcast to cluster '{cluster}' at {members}")
    client = hazelcast.HazelcastClient(
        cluster_name=cluster,
        cluster_members=members,
    )
    return client

def read_kv(key):
    c = consul.Consul()
    index, data = c.kv.get(key)
    return data["Value"].decode() if data else None

class HazelcastManager:
    def __init__(self, cluster_name="dev", instance_name=None):
        self.instance_name = instance_name or f"logging-service-{id(self)}"
        self.client = None

    def connect(self):
        """Initialize Hazelcast client"""
        try:
            self.client = create_hazelcast_client()
            self.messages_map = self.client.get_map(read_kv("map/name"))
            self.queue = self.client.get_queue(read_kv("queue/name"))
            logger.info(f"Hazelcast client connected: {self.instance_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Hazelcast: {e}")
            self.messages_map = None  # No fallback dict!
            logger.warning("Hazelcast not available")

    def disconnect(self):
        if self.client:
            self.client.shutdown()
            logger.info("Hazelcast client disconnected")

    async def put_message(self, key: str, message: str):
        try:
            if self.messages_map:
                self.messages_map.put(key, message).result()
                logger.info(f"Stored message: {key} = {message}")
            else:
                logger.warning("Hazelcast map not initialized")
        except Exception as e:
            logger.error(f"Error storing message: {e}")

    def get_message(self, key: str) -> str:
        try:
            if self.messages_map:
                return self.messages_map.get(key).result()
        except Exception as e:
            logger.error(f"Error retrieving message: {e}")
        return None

    def get_all_messages(self) -> dict:
        try:
            if self.messages_map:
                entries = self.messages_map.entry_set().result()
                return dict(entries)
        except Exception as e:
            logger.error(f"Error retrieving all messages: {e}")
        return {}

    def get_map_size(self) -> int:
        try:
            if self.messages_map:
                return self.messages_map.size().result()
        except Exception as e:
            logger.error(f"Error getting map size: {e}")
        return 0