import pytest
from logos_shift_client import Instrumentation
import asyncio

# Mock for the send_data function to capture data
mock_data_buffer = []

def mock_send_data(data, dataset="default"):
    mock_data_buffer.append((data, dataset))

@pytest.fixture
def setup_instrumentation():
    instrumentation = Instrumentation(api_key="YOUR_API_KEY")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(instrumentation._start_async_operations())
    return instrumentation

@pytest.mark.asyncio
async def test_basic_function_call(setup_instrumentation):
    @setup_instrumentation.decorator()
    def add(x, y):
        return x + y

    result = await add(1, 2)
    assert result == 3

    # Make sure its completed
    await asyncio.sleep(1)

    # Check if instrumentation captured the correct data
    assert mock_data_buffer[0][0] == {
        'input': {'x': 1, 'y': 2},
        'output': 3
    }

    setup_instrumentation.stop()

@pytest.mark.asyncio
async def test_dataset_parameter(setup_instrumentation):
    @setup_instrumentation.decorator(dataset="test_dataset")
    def subtract(x, y):
        return x - y

    result = await subtract(5, 3)
    assert result == 2

    # Make sure its completed
    await asyncio.sleep(1)

    # Check if instrumentation used the correct dataset
    assert mock_data_buffer[1][1] == "test_dataset"

    setup_instrumentation.stop()
