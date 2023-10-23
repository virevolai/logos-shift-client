import hashlib
import logging
import random

logger = logging.getLogger(__name__)


class APIRouter:
    def __init__(self, threshold=0.1, mode="never"):
        self.threshold = threshold  # precentage of requests to new API
        self.mode = mode  # "never", "random" or "user_based"
        logger.info(f"Initialized {mode} router")

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
        if self.should_route_to_new_api(user_id):
            return self.call_new_api
        # return self.call_old_api(**kwargs)
        return old_api_func

    # def call_api_async(self, old_api_func, user_id=None):
    #    if self.should_route_to_new_api(user_id):
    #        return self.call_new_api_async
    #    return old_api_func

    def call_old_api(self, **kwargs):
        raise NotImplementedError()

    async def call_new_api_async(self, **kwargs):
        raise NotImplementedError()

    def call_new_api(self, **kwargs):
        raise NotImplementedError()
