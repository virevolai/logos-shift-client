import hashlib
import logging
import random

logger = logging.getLogger(__name__)


class APIRouter:
    def __init__(self, bohita_client=None, threshold=0.1, mode="never"):
        self.bohita_client = bohita_client
        self.threshold = threshold  # precentage of requests to new API
        self.mode = mode  # "never", "random" or "user_based"
        self.call_count, self.conf_frequency = (
            0,
            1_000,
        )  # How frequently to fetch config
        logger.info(f"Initialized {mode} router")
        self._get_configuration

    def _get_configuration(self):
        try:
            logger.info("Checking for config updates")
            config = self.bohita_client.get_config()
            self.threshold = config.get("threshold", self.threshold)
            self.mode = config.get("mode", self.mode)
            self.conf_frequency = config.get("frequency", self.conf_frequency)
        except Exception:
            logger.warning(
                "Could not get configuration from server. If the problem persists, this instance might be stale"
            )

    def _get_user_hash(self, user_id):
        return int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)

    def should_route_to_new_api(self, user_id=None):
        if self.mode == "random":
            return random.random() < self.threshold
        elif self.mode == "user_based":
            if user_id:
                return self._get_user_hash(user_id) % 100 < self.threshold * 100
        return False

    def get_api_to_call(self, old_api_func, user_id=None):
        self.call_count += 1
        if self.call_count % self.conf_frequency == 0:
            self._get_configuration()
        if self.should_route_to_new_api(user_id):
            return self.call_new_api
        return old_api_func

    async def call_new_api_async(self, **kwargs):
        self.bohita_client.predict(**kwargs)

    def call_new_api(self, **kwargs):
        self.bohita_client.predict(**kwargs)
