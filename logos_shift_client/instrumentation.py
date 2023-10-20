import asyncio
import threading
from collections import deque
from tenacity import retry, wait_fixed
import logging
import time

logger = logging.getLogger(__name__)
MAX_ENTRIES = 10
CHECK_SECONDS = 5 

class BufferManager:
    # Implementing Singleton pattern
    _instance = None
    lock = threading.Lock()

    def __init__(self, check_seconds=CHECK_SECONDS):
        if getattr(self, '__initialized', False):
            return
        self.check_seconds = check_seconds
        self.__initialized = True

    def __new__(cls, check_seconds=CHECK_SECONDS, *args, **kwargs):
        with cls.lock:
            if not cls._instance:
                cls._instance = super(BufferManager, cls).__new__(cls)
                cls._instance.__initialized = False
                cls._instance.check_seconds = check_seconds
                cls._instance.buffers = []
                cls._instance.thread = threading.Thread(target=cls._instance.send_data_from_buffers, daemon=True)
                cls._instance.thread.start()
                logger.info('BufferManager: Initialized and sending thread started.')
        return cls._instance

    @retry(wait=wait_fixed(3))
    def send_data(self, data, dataset="default"):
        logger.info(f"BufferManager: Sending data to dataset {dataset}. Data: {data}")
        # Placeholder for sending data

    def send_data_from_buffers(self):
        while True:
            time.sleep(self.check_seconds)
            for buffer in self.buffers:
                with buffer["lock"]:
                    if buffer["data"]:
                        data_to_send = list(buffer["data"])
                        buffer["data"].clear()
                        for item in data_to_send:
                            # logger.debug(f'Sending {item}')
                            self.send_data(item, dataset=item["dataset"])

    def register_buffer(self, buffer, lock):
        self.buffers.append({
            "data": buffer,
            "lock": lock
        })


class Instrumentation:
    def __init__(self, api_key, max_entries=MAX_ENTRIES, check_seconds=CHECK_SECONDS):
        self.api_key, self.max_entries = api_key, max_entries
        self.buffer_A, self.buffer_B = deque(), deque()
        self.active_buffer = self.buffer_A
        self.lock = threading.Lock()
        self.buffer_manager = BufferManager(check_seconds=check_seconds)
        self.buffer_manager.register_buffer(self.buffer_A, self.lock)
        self.buffer_manager.register_buffer(self.buffer_B, self.lock)
        logger.info('Instrumentation: Initialized.')

    def handle_data(self, result, dataset, args, kwargs):
        data = {
            "input": (args, kwargs),
            "output": result,
            "dataset": dataset,
        }
        with self.lock:
            # Switch buffers if necessary
            if len(self.active_buffer) >= self.max_entries:
                logger.debug('Switching buffer')
                if self.active_buffer is self.buffer_A:
                    self.active_buffer = self.buffer_B
                else:
                    self.active_buffer = self.buffer_A
            self.active_buffer.append(data)
            # logger.debug('Added data to active buffer')
        return result

    def wrap_function(self, func, dataset, *args, **kwargs):
        logger.debug(f"Instrumentation: Wrapping function {func.__name__}. Args: {args}, Kwargs: {kwargs}")
        result = func(*args, **kwargs)
        return self.handle_data(result, dataset, args, kwargs)

    def wrap_coroutine(self, func, dataset, *args, **kwargs):
        logger.debug(f"Instrumentation: Wrapping coroutine {func.__name__}. Args: {args}, Kwargs: {kwargs}")
        async def async_inner(*a, **kw):
            result = await func(*a, **kw)
            return self.handle_data(result, dataset, a, kw)
        return async_inner(*args, **kwargs)

    def __call__(self, dataset="default"):
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

