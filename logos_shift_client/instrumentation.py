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
        self.buffer = deque()
        self.lock = threading.Lock()
        self.last_send_time = time.time()
        self.data_ready = threading.Event()
        self.thread = threading.Thread(target=self.periodic_send, daemon=True)
        self.thread.start()
        logger.info('Instrumentation: Initialized.')

    @retry(wait=wait_fixed(3))
    def send_data(self, data, dataset="default"):
        logger.info(f"Instrumentation: Sending data to dataset {dataset}. Data: {data}")
        # Placeholder for sending data

    def periodic_send(self):
        logger.info("Instrumentation: periodic_send triggered.")
        while True:
            self.data_ready.wait(timeout=10)
            with self.lock:
                logger.debug(f"Instrumentation: Inside periodic_send. Buffer length: {len(self.buffer)}, Time since last send: {time.time() - self.last_send_time}")
                if time.time() - self.last_send_time >= 10 or len(self.buffer) >= 5:
                    logger.info("Instrumentation: Sending buffered data based on periodic conditions.")
                    data_to_send = list(self.buffer)
                    self.buffer.clear()
                    for item in data_to_send:
                        dataset_value = item.pop("dataset", "default")
                        self.send_data(item, dataset=dataset_value)
                    self.last_send_time = time.time()
                else:
                    logger.debug("Instrumentation: Conditions not met for sending data.")
            self.data_ready.clear()

    def wrap_function(self, func, dataset, *args, **kwargs):
        logger.debug(f"Instrumentation: Wrapping function {func.__name__}. Args: {args}, Kwargs: {kwargs}")
        result = func(*args, **kwargs)
        data = {
            "input": (args, kwargs),
            "output": result,
            "dataset": dataset,
        }
        with self.lock:
            logger.debug(f"Instrumentation: Adding data to buffer after function execution.")
            self.buffer.append(data)
            self.data_ready.set()
        return result

    def wrap_coroutine(self, func, dataset, *args, **kwargs):
        logger.debug(f"Instrumentation: Wrapping coroutine {func.__name__}. Args: {args}, Kwargs: {kwargs}")
        async def async_inner(*a, **kw):
            result = await func(*a, **kw)
            data = {
                "input": (a, kw),
                "output": result,
                "dataset": dataset,
            }
            with self.lock:
                logger.debug(f"Instrumentation: Adding data to buffer after coroutine execution.")
                self.buffer.append(data)
                self.data_ready.set()
            return result
        return async_inner(*args, **kwargs)

    def decorator(self, dataset="default"):
        def outer(func):
            def inner(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    logger.debug("Instrumentation: Detected coroutine.")
                    return self.wrap_coroutine(func, dataset, *args, **kwargs)
                else:
                    logger.debug("Instrumentation: Detected synchronous function.")
                    return self.wrap_function(func, dataset, *args, **kwargs)
            return inner
        return outer

