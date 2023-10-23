import pytest

from logos_shift_client import APIRouter

# Mocks for old and new APIs to capture calls
old_api_called = False
new_api_called = False


def mock_old_api(**kwargs):
    global old_api_called
    old_api_called = True
    return "old_api_response"


def mock_new_api(**kwargs):
    global new_api_called
    new_api_called = True
    return "new_api_response"


@pytest.fixture
def setup_router():
    router = APIRouter(threshold=0.5, mode="random")
    router.call_old_api = mock_old_api
    router.call_new_api = mock_new_api
    return router


def test_random_routing(setup_router):
    global old_api_called, new_api_called

    # Resetting the mock flags
    old_api_called, new_api_called = False, False

    func_to_call = setup_router.get_api_to_call(mock_old_api)
    result = func_to_call()

    assert result in ["old_api_response", "new_api_response"]
    assert old_api_called or new_api_called, "Neither old nor new API was called"


def test_user_based_routing(setup_router):
    global old_api_called, new_api_called

    # Changing the mode to user_based
    setup_router.mode = "user_based"

    # Resetting the mock flags
    old_api_called, new_api_called = False, False

    func_to_call = setup_router.get_api_to_call(mock_old_api, user_id="test_user")
    result = func_to_call()

    assert result in ["old_api_response", "new_api_response"]
    assert old_api_called or new_api_called, "Neither old nor new API was called"


def test_async_routing(setup_router):
    global old_api_called, new_api_called

    # Mocking async versions of the APIs
    async def async_mock_old_api(**kwargs):
        global old_api_called
        old_api_called = True
        return "old_api_response"

    async def async_mock_new_api(**kwargs):
        global new_api_called
        new_api_called = True
        return "new_api_response"

    setup_router.call_old_api = async_mock_old_api
    setup_router.call_new_api = async_mock_new_api

    # Resetting the mock flags
    old_api_called, new_api_called = False, False

    async def run_test():
        func_to_call = setup_router.get_api_to_call(async_mock_old_api)
        result = await func_to_call()
        assert result in ["old_api_response", "new_api_response"]
        assert old_api_called or new_api_called, "Neither old nor new API was called"

    # Run the async test
    import asyncio

    asyncio.run(run_test())
