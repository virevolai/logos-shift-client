import asyncio
from collections import deque
from tenacity import retry, wait_fixed

class Instrumentation:
    def __init__(self, api_key):
        self.api_key = api_key
        self.buffer1 = deque()
        self.buffer2 = deque()
        self.active_buffer = self.buffer1
        self.lock = asyncio.Lock()
        self.last_send_time = None
        self.started = False

    def start_async_operations(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._start_async_operations())

    async def _start_async_operations(self):
        self.last_send_time = asyncio.get_event_loop().time()
        asyncio.create_task(self.periodic_send())
        self.started = True

    def stop(self):
        self._periodic_send_task.cancel()
        self.started = False

    @retry(wait=wait_fixed(3))
    async def send_data(self, data, dataset):
        # Send data to instrumentation endpoint
        # Use tenacity to handle retries in case of failures
        # Example: await aiohttp.post(url, data=data, headers={"API-Key": self.api_key})
        pass

    async def periodic_send(self):
        while True:
            await asyncio.sleep(1)  # Check every second
            async with self.lock:
                if asyncio.get_event_loop().time() - self.last_send_time >= 60 or len(self.active_buffer) >= 100:
                    data = list(self.active_buffer)
                    self.active_buffer.clear()
                    if self.active_buffer is self.buffer1:
                        self.active_buffer = self.buffer2
                    else:
                        self.active_buffer = self.buffer1
                    await self.send_data(data, dataset="default")
                    self.last_send_time = asyncio.get_event_loop().time()

    def wrap(self, func, dataset="default"):
        if not self.started:
            self.start_async_operations()

        async def inner(*args, **kwargs):
            async with self.lock:
                self.active_buffer.append({"input": (args, kwargs), "output": None})
            result = await func(*args, **kwargs)
            async with self.lock:
                self.active_buffer[-1]["output"] = result
            return result
        return inner

    #def decorator(self, dataset="default"):
    #    def outer(func):
    #        return self.wrap(func, dataset)
    #    return outer

    def decorator(self, dataset="default"):
        def outer(func):
            if asyncio.iscoroutinefunction(func):
                return self.wrap(func, dataset)
            else:
                async def async_func(*args, **kwargs):
                    return func(*args, **kwargs)
                return self.wrap(async_func, dataset)
        return outer

