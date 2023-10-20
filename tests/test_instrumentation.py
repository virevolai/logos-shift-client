import pytest
from logos_shift_client import Instrumentation
import time
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



# Mock for the send_data function to capture data
mock_data_buffer = []

def mock_send_data(data, dataset="default"):
    print(f'Sending ({data}, {dataset})')
    mock_data_buffer.append((data, dataset))

def wait_for_data(buffer, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if buffer:
            return True
        time.sleep(0.1)  # Check every 100 milliseconds
    return False

@pytest.fixture
def setup_instrumentation():
    instrumentation = Instrumentation(api_key="YOUR_API_KEY", max_entries=1, check_seconds=0.5)
    
    # Override the actual send_data method with our mock for testing
    instrumentation.buffer_manager.send_data = mock_send_data
    
    print('config: ', instrumentation.max_entries, instrumentation.buffer_manager.check_seconds, instrumentation.buffer_manager.send_data)
    return instrumentation

def test_basic_function_call(setup_instrumentation):
    @setup_instrumentation()
    def add(x, y):
        return x + y

    mock_data_buffer.clear()
    result = add(1, 2)
    assert result == 3

    time.sleep(1)
    print(f"mock_data_buffer: {mock_data_buffer}")
    assert wait_for_data(mock_data_buffer), "Timeout waiting for data"

    # Check if instrumentation captured the correct data
    expected_data = {
        'input': ((1, 2), {}),
        'output': 3,
        'dataset': 'default',
    }
    assert any(item[0] == expected_data for item in mock_data_buffer), "Expected data not found in mock_data_buffer"


def test_dataset_parameter(setup_instrumentation):
    @setup_instrumentation(dataset="test_dataset")
    def subtract(x, y):
        return x - y

    mock_data_buffer.clear()
    result = subtract(5, 3)
    assert result == 2

    time.sleep(1)
    print(f"mock_data_buffer: {mock_data_buffer}")
    assert wait_for_data(mock_data_buffer), "Timeout waiting for data"

    assert any(item[1] == "test_dataset" for item in mock_data_buffer), "Expected dataset not found in mock_data_buffer"



