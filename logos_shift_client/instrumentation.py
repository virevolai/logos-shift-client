import asyncio
import threading
from collections import deque
from tenacity import retry, wait_fixed
import logging
import time

logger = logging.getLogger(__name__)


class Instrumentation:
    def __init__(self, api_key):
        self.api_key = api_key
        self.buffer1 = deque()
        self.buffer2 = deque()
        self.active_buffer = self.buffer1
        self.lock = threading.Lock()
        self.last_send_time = time.time()
        self.data_ready = threading.Event()
        self.thread = threading.Thread(target=self.periodic_send, daemon=True)
        self.thread.start()
        logger.info('Started')

    @retry(wait=wait_fixed(3))
    def send_data(self, data, dataset="default"):
        logger.info('sending data')
        # Send data to instrumentation endpoint
        # Use tenacity to handle retries in case of failures
        # Example: requests.post(url, data=data, headers={"API-Key": self.api_key})
        pass

    def periodic_send(self):
        while True:
            self.data_ready.wait(timeout=60)
            with self.lock:
                logger.info(f"Checking buffer size: {len(self.active_buffer)} and time elapsed: {time.time() - self.last_send_time}")
                if time.time() - self.last_send_time >= 60 or len(self.active_buffer) >= 100:
                    logger.info("Inside periodic_send: Conditions met for sending data")
                    data = list(self.active_buffer)
                    buffer_to_clear = self.active_buffer
                    if self.active_buffer is self.buffer1:
                        self.active_buffer = self.buffer2
                    else:
                        self.active_buffer = self.buffer1
                    for item in data:
                        dataset_value = item.get("dataset", "default")
                        self.send_data(item, dataset=dataset_value)
                    # self.active_buffer.clear()
                    buffer_to_clear.clear() # Handle race condition
                    self.last_send_time = time.time()
                else:
                    logger.info("Inside periodic_send: Conditions not met for sending data")
            self.data_ready.clear()

    def wrap(self, func, dataset="default"):
        if asyncio.iscoroutinefunction(func):
            logger.info('Async wrapper')
            async def async_inner(*args, **kwargs):
                with self.lock:
                    logger.info(f"Adding data to buffer: {args}, {kwargs}")
                    self.active_buffer.append({
                        "input": (args, kwargs),
                        "output": None,
                        "dataset": dataset,
                    })
                    self.data_ready.set()
                result = await func(*args, **kwargs)
                with self.lock:
                    self.active_buffer[-1]["output"] = result
                return result
            return async_inner
        else:
            logger.info('Sync wrapper')
            def sync_inner(*args, **kwargs):
                with self.lock:
                    logger.info(f"Adding data to buffer: {args}, {kwargs}")
                    self.active_buffer.append({
                        "input": (args, kwargs),
                        "output": None,
                        "dataset": dataset,
                    })
                    self.data_ready.set()
                result = func(*args, **kwargs)
                with self.lock:
                    self.active_buffer[-1]["output"] = result
                return result
            return sync_inner

    def decorator(self, dataset="default"):
        def outer(func):
            return self.wrap(func, dataset)
        return outer
