import requests
import httpx
import logging

BASE_URL = "https://logos-shift-sink-6kso2cgttq-uc.a.run.app"
TIMEOUT = 10  # seconds
logger = logging.getLogger(__name__)


class BohitaClient:
    def __init__(self, api_key: str):
        if api_key is None:
            logging.warning(
                "No API KEY provided. No data will be sent to Bohita and automatic routing will not happen"
            )
            self.headers = None
        else:
            self.headers = {
                "Content-Type": "application/json",
                "Bohita-Auth": f"Bearer {api_key}",
            }
        self.async_client = httpx.AsyncClient(headers=self.headers, timeout=TIMEOUT)

    def post_instrumentation_data(self, data, dataset):
        if not self.headers:
            return
        try:
            response = requests.post(
                f"{BASE_URL}/instrumentation/",
                headers=self.headers,
                json={**data, "dataset": dataset},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to post instrumentation data: %s", str(e))

    async def post_instrumentation_data_async(self, data, dataset):
        if not self.headers:
            return
        try:
            response = await self.async_client.post(
                f"{BASE_URL}/instrumentation/", json={**data, "dataset": dataset}
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            logger.error("Failed to post instrumentation data: %s", str(e))

    def get_config(self):
        if not self.headers:
            return {}
        try:
            response = requests.get(
                f"{BASE_URL}/config", headers=self.headers, timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("Failed to get configuration: %s", str(e))
            return {}

    async def get_config_async(self):
        if not self.headers:
            return {}
        try:
            response = await self.async_client.get(f"{BASE_URL}/config")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Failed to get configuration: %s", str(e))
            return {}

    def predict(self, **kwargs):
        if not self.headers:
            return
        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                headers=self.headers,
                json=kwargs,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("Failed to make prediction: %s", str(e))

    async def predict_async(self, **kwargs):
        if not self.headers:
            return
        try:
            response = await self.async_client.post(f"{BASE_URL}/predict", json=kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error("Failed to make prediction: %s", str(e))
