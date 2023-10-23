import requests

BASE_URL = "https://logos-shift-sink-6kso2cgttq-uc.a.run.app"


# from pydantic import BaseModel, UUID4
# from typing import Dict, Tuple, Optional
#
# class InstrumentationData(BaseModel):
#    input: Optional[Tuple[Tuple[int, int], Dict[str, Any]]] = None
#    output: Optional[Any] = None
#    bohita_logos_shift_id: Optional[UUID4] = None
#    feedback: Optional[str] = None
#    dataset: str
#    metadata: Dict[str, Any]


class BohitaClient:
    def __init__(self, api_key: str):
        self.headers = {
            "Content-Type": "application/json",
            "Bohita-Auth": f"Bearer {api_key}",
        }

    def post_instrumentation_data(self, data, dataset) -> requests.Response:
        response = requests.post(
            f"{BASE_URL}/instrumentation/",
            headers=self.headers,
            json={**data, "dataset": dataset},
        )
        response.raise_for_status()

    def get_config(self) -> requests.Response:
        response = requests.get(f"{BASE_URL}/config", headers=self.headers)
        return response.json()

    def predict(self, **kwargs):
        response = requests.post(
            f"{BASE_URL}/predict", headers=self.headers, json=kwargs
        )
        return response.json()
