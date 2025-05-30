import os
from dotenv import load_dotenv

# Wczytanie zmiennych środowiskowych z .env
load_dotenv()

try:
    import redis
except ImportError:
    redis = None


def get_redis_client():
    """
    Próba połączenia z Redis na podstawie REDIS_URL.
    Jeśli Redis lub biblioteka nie są dostępne, zwraca None.
    """
    url = os.getenv("REDIS_URL", "")
    if not url or not redis:
        print("⚠️ REDIS_URL is not set or redis library missing — using in-memory fallback.")
        return None
    try:
        client = redis.from_url(url, decode_responses=True)
        # Test connect
        client.ping()
        print("✅ Connected to Redis at:", url)
        return client
    except Exception as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("⚠️ Falling back to in-memory store.")
        return None


class AgentState:
    """
    Zarządza stanem agenta (uruchomiony/zatrzymany).
    Stosuje Redis, jeśli dostępny, w przeciwnym razie pamięć lokalną.
    """
    def __init__(self):
        self._client = get_redis_client()
        self._in_memory = {} if self._client is None else None
        self._key = "agent:is_running"

    def start(self):
        """Ustawia stan agenta na uruchomiony."""
        if self._client:
            self._client.set(self._key, "1")
        else:
            self._in_memory[self._key] = "1"
        print("➡️ Agent state set to RUNNING")

    def stop(self):
        """Ustawia stan agenta na zatrzymany."""
        if self._client:
            self._client.set(self._key, "0")
        else:
            self._in_memory[self._key] = "0"
        print("➡️ Agent state set to STOPPED")

    @property
    def is_running(self) -> bool:
        """Zwraca True jeśli agent jest uruchomiony."""
        if self._client:
            val = self._client.get(self._key)
        else:
            val = self._in_memory.get(self._key, "0")
        return val == "1"


# Singleton: globalna instancja gotowa do importu
agent_state = AgentState()


if __name__ == "__main__":
    # Test modułu standalone
    print("Initial state:", agent_state.is_running)
    agent_state.start()
    print("After start():", agent_state.is_running)
    agent_state.stop()
    print("After stop():", agent_state.is_running)
