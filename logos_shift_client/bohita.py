import requests
import logging

BASE_URL = "https://logos-shift-sink-6kso2cgttq-uc.a.run.app"
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

    def post_instrumentation_data(self, data, dataset) -> requests.Response:
        if not self.headers:
            return
        response = requests.post(
            f"{BASE_URL}/instrumentation/",
            headers=self.headers,
            json={**data, "dataset": dataset},
        )
        response.raise_for_status()

    def get_config(self) -> requests.Response:
        if not self.headers:
            return
        response = requests.get(f"{BASE_URL}/config", headers=self.headers)
        return response.json()

    def predict(self, **kwargs):
        if not self.headers:
            return
        response = requests.post(
            f"{BASE_URL}/predict", headers=self.headers, json=kwargs
        )
        return response.json()
