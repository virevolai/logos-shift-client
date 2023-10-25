import asyncio
import logging
import threading
import time
import uuid
from pathlib import Path
from collections import deque
from typing import Optional, Union

from tenacity import retry, wait_fixed

from .bohita import BohitaClient
from .router import APIRouter

logger = logging.getLogger(__name__)
MAX_ENTRIES = 10
CHECK_SECONDS = 5


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class BufferManager(metaclass=SingletonMeta):
    """
    A singleton class responsible for managing data buffers and sending data to a remote server.

    Attributes:
        bohita_client: An instance of BohitaClient used to send data to the remote server.
        check_seconds: The interval in seconds between checks to send data from the buffers.
        filepath: The file path for local data storage. If None, data is not stored locally.
        buffers: A list of data buffers.
        thread: The thread responsible for sending data from the buffers.
    """

    _instance = None
    lock = threading.Lock()

    def __init__(
        self,
        bohita_client: BohitaClient,
        check_seconds: int = CHECK_SECONDS,
        filename: Optional[Union[str, Path]] = None,
    ):
        self.bohita_client = bohita_client
        self.check_seconds = check_seconds
        self.open_handle(filename)
        self.buffers = []
        self.thread = threading.Thread(target=self.send_data_from_buffers, daemon=True)
        self.thread.start()
        logger.info("BufferManager: Initialized and sending thread started.")

    def open_handle(self, filename: str):
        if filename:
            logdir = Path(filename).parent
            if not logdir.exists():
                raise Exception(f"Directory {logdir} does not exist!")
            self.file_handle = open(Path(filename), "a", buffering=1)
        else:
            self.file_handle = None

    def __del__(self):
        if self.file_handle:
            self.file_handle.close()

    def _write_to_local(self, data):
        if self.file_handle:
            for item in data:
                self.file_handle.write(str(item) + "\n")

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
    """
    LogosShift is a tool for capturing, logging, and optionally sending function call data to a remote server.

    It allows developers to easily instrument their functions, capturing input arguments, output results, metadata, and optionally sending this data to the Bohita platform for further analysis. Data can also be stored locally.

    Attributes:
        bohita_client (BohitaClient): The client used to send data to the Bohita platform.
        max_entries (int): The maximum number of entries to store in a buffer before switching to the next buffer.
        buffer_A (collections.deque): The first data buffer.
        buffer_B (collections.deque): The second data buffer.
        active_buffer (collections.deque): The currently active data buffer.
        lock (threading.Lock): A lock to ensure thread-safety when modifying the buffers.
        buffer_manager (BufferManager): The manager for handling data buffers and sending data.
        router (APIRouter): The router for determining which API to call based on the function and user.

    Examples:
        >>> logos_shift = LogosShift(api_key="YOUR_API_KEY")
        >>> @logos_shift()
        ... def add(x, y):
        ...     return x + y
        ...
        >>> result = add(1, 2)

        To provide feedback:
        >>> logos_shift.provide_feedback(result['bohita_logos_shift_id'], "success")

        To specify a dataset:
        >>> @logos_shift(dataset="sales")
        ... def add_sales(x, y):
        ...     return x + y

        Using metadata:
        >>> @logos_shift()
        ... def multiply(x, y, logos_shift_metadata={"user_id": "12345"}):
        ...     return x * y

        To store data locally:
        >>> logos_shift = LogosShift(api_key="YOUR_API_KEY", filename="api_calls.log")

        To disable sending data to Bohita:
        >>> logos_shift = LogosShift(api_key=None, filename="api_calls.log")
    """

    def __init__(
        self,
        api_key,
        bohita_client=None,
        router=None,
        max_entries=MAX_ENTRIES,
        check_seconds=CHECK_SECONDS,
        filename=None,
    ):
        """
        Initializes a new instance of LogosShift.

        Args:
            api_key (str): Your API key for the Bohita platform.
            bohita_client (Optional[BohitaClient]): An optional instance of BohitaClient. If not provided, a new instance will be created.
            router (Optional[APIRouter]): An optional instance of APIRouter. If not provided, a new instance will be created.
            max_entries (int): The maximum number of entries to store in a buffer before switching to the next buffer. Default is 10.
            check_seconds (int): The interval in seconds between checks to send data from the buffers. Default is 5.
            filename (Optional[Union[str, Path]]): The file path for local data storage. If None, data is not stored locally.

        Examples:
            >>> logos_shift = LogosShift(api_key="YOUR_API_KEY")
            >>> logos_shift = LogosShift(api_key="YOUR_API_KEY", filename="api_calls.log")
        """
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

    def _wrap_common(self, func, dataset, args, kwargs, is_async):
        logger.debug(
            f"LogosShift: Wrapping {'coroutine' if is_async else 'function'} {func.__name__}. Args: {args}, Kwargs: {kwargs}"
        )
        metadata = kwargs.pop("logos_shift_metadata", {})
        metadata["function"] = func.__name__
        if self.router:
            func_to_call = self.router.get_api_to_call(
                func, metadata.get("user_id", None)
            )
        else:
            func_to_call = func

        return func_to_call, args, kwargs, metadata

    def wrap_function(self, func, dataset, *args, **kwargs):
        func_to_call, args, kwargs, metadata = self._wrap_common(
            func, dataset, args, kwargs, False
        )
        result = func_to_call(*args, **kwargs)
        return self.handle_data(result, dataset, args, kwargs, metadata)

    async def wrap_coroutine(self, func, dataset, *args, **kwargs):
        func_to_call, args, kwargs, metadata = await self._wrap_common(
            func, dataset, args, kwargs, True
        )
        result = await func_to_call(*args, **kwargs)
        return self.handle_data(result, dataset, args, kwargs, metadata)

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
        """
        Provides feedback for a specific function call.

        Args:
            bohita_logos_shift_id (str): The unique identifier for the function call.
            feedback (str): The feedback string.

        Examples:
            >>> logos_shift.provide_feedback("unique_id_123", "success")
        """
        feedback_data = {
            "bohita_logos_shift_id": bohita_logos_shift_id,
            "feedback": feedback,
            "dataset": "unknown",
        }
        with self.lock:
            self.active_buffer.append(feedback_data)
