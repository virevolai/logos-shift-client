import hashlib
import logging
import random
import asyncio

logger = logging.getLogger(__name__)


class APIRouter:
    """
    APIRouter is responsible for routing API calls based on the provided configuration.

    It supports three modes:
    - "never": Always use the old API.
    - "random": Randomly choose between the old and new API based on a threshold.
    - "user_based": Decide based on a hash of the user ID.

    Attributes:
        bohita_client (BohitaClient): The client used to communicate with the Bohita platform.
        threshold (float): The percentage of requests to route to the new API. Default is 0.1 (10%).
        mode (str): The routing mode. Can be "never", "random", or "user_based". Default is "never".
        call_count (int): The number of API calls made.
        conf_frequency (int): How frequently to fetch configuration updates from the server.

    Examples:
        >>> router = APIRouter(bohita_client, threshold=0.2, mode="random")
        >>> api_to_call = router.get_api_to_call(old_api_func)
    """

    def __init__(self, bohita_client=None, threshold=0.1, mode="never"):
        """
        Initializes a new instance of APIRouter.

        Args:
            bohita_client (Optional[BohitaClient]): An instance of BohitaClient used to communicate with the Bohita platform.
            threshold (float): The percentage of requests to route to the new API. Default is 0.1 (10%).
            mode (str): The routing mode. Can be "never", "random", or "user_based". Default is "never".
        """
        self.bohita_client = bohita_client
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold  # precentage of requests to new API
        self.mode = mode  # "never", "random" or "user_based"
        self.call_count, self.conf_frequency = (
            0,
            1_000,
        )  # How frequently to fetch config
        logger.info(f"Initialized {mode} router")
        # Fails in async context, disable for now
        # self._get_configuration()

    async def _get_configuration_common(self, is_async):
        """
        Fetches the routing configuration from the Bohita platform and updates the router's settings.

        This method is called periodically based on the conf_frequency setting.
        """
        try:
            logger.info("Checking for config updates")
            if is_async:
                config = await self.bohita_client.get_config_async()
            else:
                config = self.bohita_client.get_config()
            self.threshold = config.get("threshold", self.threshold)
            self.mode = config.get("mode", self.mode)
            self.conf_frequency = config.get("frequency", self.conf_frequency)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.warning("Could not get configuration from server: %s", str(e))
            logger.warning("If the problem persists, this instance might be stale")

    def _get_configuration(self):
        asyncio.run(self._get_configuration_common(False))

    async def _get_configuration_async(self):
        await self._get_configuration_common(True)

    def _get_user_hash(self, user_id):
        return int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)

    def should_route_to_new_api(self, user_id=None):
        """
        Determines whether the next API call should be routed to the new API based on the current mode and threshold.

        Args:
            user_id (Optional[str]): The user ID for user-based routing. Required if mode is "user_based".

        Returns:
            bool: True if the call should be routed to the new API, False otherwise.
        """
        if self.mode == "random":
            return random.random() < self.threshold
        elif self.mode == "user_based":
            if user_id:
                return self._get_user_hash(user_id) % 100 < self.threshold * 100
        return False

    def get_api_to_call(self, old_api_func, user_id=None):
        """
        Determines which API function to call based on the routing configuration.

        Args:
            old_api_func (callable): The old API function.
            user_id (Optional[str]): The user ID for user-based routing.

        Returns:
            callable: The API function to call.
        """
        self.call_count += 1
        if self.call_count % self.conf_frequency == 0:
            self._get_configuration()
        if self.should_route_to_new_api(user_id):
            return self.call_new_api
        return old_api_func

    async def get_api_to_call_async(self, old_api_func, user_id=None):
        """
        Determines which API function to call based on the routing configuration.

        Args:
            old_api_func (callable): The old API function.
            user_id (Optional[str]): The user ID for user-based routing.

        Returns:
            callable: The API function to call.
        """
        self.call_count += 1
        if self.call_count % self.conf_frequency == 0:
            await self._get_configuration_async()
        if self.should_route_to_new_api(user_id):
            return self.call_new_api_async
        return old_api_func

    async def call_new_api_async(self, **kwargs):
        await self.bohita_client.predict_async(**kwargs)

    def call_new_api(self, **kwargs):
        self.bohita_client.predict(**kwargs)
