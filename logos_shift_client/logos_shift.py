import asyncio
import logging
import threading
import time
import uuid
from pathlib import Path
from collections import deque

from tenacity import retry, wait_fixed

from .bohita import BohitaClient
from .router import APIRouter

logger = logging.getLogger(__name__)
MAX_ENTRIES = 10
CHECK_SECONDS = 5


class BufferManager:
    # Implementing Singleton pattern
    _instance = None
    lock = threading.Lock()

    def __init__(self, bohita_client, check_seconds=CHECK_SECONDS, filename=None):
        if getattr(self, "__initialized", False):
            return
        self.bohita_client = bohita_client
        self.check_seconds = check_seconds
        self.filepath = self.check_filename(filename)
        self.__initialized = True

    def __new__(
        cls, bohita_client, check_seconds=CHECK_SECONDS, filename=None, *args, **kwargs
    ):
        with cls.lock:
            if not cls._instance:
                cls._instance = super(BufferManager, cls).__new__(cls)
                cls._instance.__initialized = False
                cls._instance.bohita_client = bohita_client
                cls._instance.check_seconds = check_seconds
                cls._instance.filepath = cls._instance.check_filename(filename)
                cls._instance.buffers = []
                cls._instance.thread = threading.Thread(
                    target=cls._instance.send_data_from_buffers, daemon=True
                )
                cls._instance.thread.start()
                logger.info("BufferManager: Initialized and sending thread started.")
        return cls._instance

    def check_filename(self, filename: str):
        if filename:
            logdir = Path(filename).parent
            if not logdir.exists():
                raise Exception(f"Directory {logdir} does not exist!")
        return Path(filename) if filename else None

    def _write_to_local(self, data):
        if self.filepath:
            with self.filepath.open("a") as file_handle:
                for item in data:
                    file_handle.write(str(item) + "\n")

    @retry(wait=wait_fixed(3))
    def send_data(self, data, dataset="default"):
        logger.info(f"BufferManager: Sending data to dataset {dataset}. Data: {data}")
        self.bohita_client.post_instrumentation_data(data, dataset)
        self._write_to_local(data)

    def send_data_from_buffers(self):
        while True:
            time.sleep(self.check_seconds)
            for buffer in self.buffers:
                with buffer["lock"]:
                    if buffer["data"]:
                        data_to_send = list(buffer["data"])
                        buffer["data"].clear()
                        for item in data_to_send:
                            logger.debug(f"Sending {item}")
                            self.send_data(item, dataset=item["dataset"])

    def register_buffer(self, buffer, lock):
        self.buffers.append({"data": buffer, "lock": lock})


class LogosShift:
    def __init__(
        self,
        api_key,
        bohita_client=None,
        router=None,
        max_entries=MAX_ENTRIES,
        check_seconds=CHECK_SECONDS,
        filename=None,
    ):
        # self.api_key, self.max_entries = api_key, max_entries
        self.max_entries = max_entries
        self.bohita_client = (
            bohita_client if bohita_client else BohitaClient(api_key=api_key)
        )
        self.buffer_A, self.buffer_B = deque(), deque()
        self.active_buffer = self.buffer_A
        self.lock = threading.Lock()
        self.buffer_manager = BufferManager(
            bohita_client=self.bohita_client,
            check_seconds=check_seconds,
            filename=filename,
        )
        self.buffer_manager.register_buffer(self.buffer_A, self.lock)
        self.buffer_manager.register_buffer(self.buffer_B, self.lock)
        self.router = router if router else APIRouter(bohita_client=self.bohita_client)
        logger.info("LogosShift: Initialized.")

    def handle_data(self, result, dataset, args, kwargs, metadata):
        if isinstance(result, dict):
            result["bohita_logos_shift_id"] = str(uuid.uuid4())
        data = {
            "input": (args, kwargs),
            "output": result,
            "dataset": dataset,
            "metadata": metadata,
        }
        with self.lock:
            # Switch buffers if necessary
            if len(self.active_buffer) >= self.max_entries:
                logger.debug("Switching buffer")
                if self.active_buffer is self.buffer_A:
                    self.active_buffer = self.buffer_B
                else:
                    self.active_buffer = self.buffer_A
            self.active_buffer.append(data)
            logger.debug("Added data to active buffer")
        return result

    def wrap_function(self, func, dataset, *args, **kwargs):
        logger.debug(
            f"LogosShift: Wrapping function {func.__name__}. Args: {args}, Kwargs: {kwargs}"
        )
        metadata = kwargs.pop("logos_shift_metadata", {})
        metadata["function"] = func.__name__
        if self.router:
            func_to_call = self.router.get_api_to_call(
                func, metadata.get("user_id", None)
            )
        else:
            func_to_call = func
        result = func_to_call(*args, **kwargs)
        return self.handle_data(result, dataset, args, kwargs, metadata)

    def wrap_coroutine(self, func, dataset, *args, **kwargs):
        logger.debug(
            f"LogosShift: Wrapping coroutine {func.__name__}. Args: {args}, Kwargs: {kwargs}"
        )
        metadata = kwargs.pop("logos_shift_metadata", {})
        metadata["function"] = func.__name__

        async def async_inner(*a, **kw):
            if self.router:
                func_to_call = await self.router.get_api_to_call(
                    func, metadata.get("user_id", None)
                )
            else:
                func_to_call = func
            result = await func_to_call(*a, **kw)
            return self.handle_data(result, dataset, a, kw, metadata)

        return async_inner(*args, **kwargs)

    def __call__(self, dataset="default"):
        def outer(func):
            def inner(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    logger.debug("LogosShift: Detected coroutine.")
                    return self.wrap_coroutine(func, dataset, *args, **kwargs)
                else:
                    logger.debug("LogosShift: Detected synchronous function.")
                    return self.wrap_function(func, dataset, *args, **kwargs)

            return inner

        return outer

    def provide_feedback(self, bohita_logos_shift_id, feedback):
        feedback_data = {
            "bohita_logos_shift_id": bohita_logos_shift_id,
            "feedback": feedback,
            "dataset": "unknown",
        }
        with self.lock:
            self.active_buffer.append(feedback_data)
