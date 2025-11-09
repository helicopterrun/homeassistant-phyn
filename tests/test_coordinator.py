"""Test the Phyn coordinator."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.phyn.update_coordinator import PhynDataUpdateCoordinator
from custom_components.phyn.devices.pp import PhynPlusDevice
from custom_components.phyn.devices.pc import PhynClassicDevice
from custom_components.phyn.devices.pw import PhynWaterSensorDevice


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.device = MagicMock()
    client.device.get_state = AsyncMock(return_value={
        "product_code": "PP1",
        "serial_number": "test-serial",
        "fw_version": "1.0.0",
        "online_status": {"v": "online"}
    })
    return client


async def test_coordinator_initialization(hass: HomeAssistant, mock_api_client):
    """Test coordinator initialization."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client,
        update_interval=timedelta(seconds=60)
    )
    
    assert coordinator.hass == hass
    assert coordinator.api_client == mock_api_client
    assert len(coordinator.devices) == 0


async def test_coordinator_add_phyn_plus_device(hass: HomeAssistant, mock_api_client):
    """Test adding a Phyn Plus device to coordinator."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    coordinator.add_device("test-home-id", "test-device-id", "PP1")
    
    assert len(coordinator.devices) == 1
    assert isinstance(coordinator.devices[0], PhynPlusDevice)
    assert coordinator.devices[0].id == "test-device-id"


async def test_coordinator_add_phyn_plus_v2_device(hass: HomeAssistant, mock_api_client):
    """Test adding a Phyn Plus V2 device to coordinator."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    coordinator.add_device("test-home-id", "test-device-id", "PP2")
    
    assert len(coordinator.devices) == 1
    assert isinstance(coordinator.devices[0], PhynPlusDevice)


async def test_coordinator_add_phyn_classic_device(hass: HomeAssistant, mock_api_client):
    """Test adding a Phyn Classic device to coordinator."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    coordinator.add_device("test-home-id", "test-device-id", "PC1")
    
    assert len(coordinator.devices) == 1
    assert isinstance(coordinator.devices[0], PhynClassicDevice)
    assert coordinator.devices[0].id == "test-device-id"


async def test_coordinator_add_water_sensor_device(hass: HomeAssistant, mock_api_client):
    """Test adding a Phyn Water Sensor device to coordinator."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    coordinator.add_device("test-home-id", "test-device-id", "PW1")
    
    assert len(coordinator.devices) == 1
    assert isinstance(coordinator.devices[0], PhynWaterSensorDevice)
    assert coordinator.devices[0].id == "test-device-id"


async def test_coordinator_add_multiple_devices(hass: HomeAssistant, mock_api_client):
    """Test adding multiple devices to coordinator."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    coordinator.add_device("test-home-id", "device-1", "PP1")
    coordinator.add_device("test-home-id", "device-2", "PC1")
    coordinator.add_device("test-home-id", "device-3", "PW1")
    
    assert len(coordinator.devices) == 3


async def test_coordinator_update_data(hass: HomeAssistant, mock_api_client):
    """Test coordinator data update."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Add a device
    coordinator.add_device("test-home-id", "test-device-id", "PP1")
    
    # Mock the device's async_update_data
    coordinator.devices[0].async_update_data = AsyncMock()
    
    # Call update
    await coordinator._async_update_data()
    
    # Verify device update was called
    coordinator.devices[0].async_update_data.assert_called_once()


async def test_coordinator_update_data_error(hass: HomeAssistant, mock_api_client):
    """Test coordinator handles update errors."""
    from aiophyn.errors import RequestError
    
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Add a device
    coordinator.add_device("test-home-id", "test-device-id", "PP1")
    
    # Mock the device's async_update_data to raise an error
    coordinator.devices[0].async_update_data = AsyncMock(
        side_effect=RequestError("Connection failed")
    )
    
    # Call update and expect UpdateFailed
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_async_setup(hass: HomeAssistant, mock_api_client):
    """Test coordinator async setup."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Add devices
    coordinator.add_device("test-home-id", "device-1", "PP1")
    coordinator.add_device("test-home-id", "device-2", "PC1")
    
    # Mock device setup methods
    for device in coordinator.devices:
        device.async_setup = AsyncMock()
    
    # Call setup
    await coordinator.async_setup()
    
    # Verify all devices were set up
    for device in coordinator.devices:
        device.async_setup.assert_called_once()


async def test_coordinator_update_data_timeout(hass: HomeAssistant, mock_api_client):
    """Test coordinator handles timeout during update."""
    import asyncio
    
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Add a device
    coordinator.add_device("test-home-id", "test-device-id", "PP1")
    
    # Mock the device's async_update_data to timeout
    async def slow_update():
        await asyncio.sleep(30)
    
    coordinator.devices[0].async_update_data = slow_update
    
    # Call update and expect timeout/UpdateFailed
    with pytest.raises((UpdateFailed, asyncio.TimeoutError)):
        await coordinator._async_update_data()


async def test_coordinator_devices_property(hass: HomeAssistant, mock_api_client):
    """Test coordinator devices property."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Initially empty
    assert coordinator.devices == []
    
    # Add devices
    coordinator.add_device("test-home-id", "device-1", "PP1")
    coordinator.add_device("test-home-id", "device-2", "PC1")
    
    # Check devices property
    devices = coordinator.devices
    assert len(devices) == 2
    assert all(hasattr(d, 'id') for d in devices)


async def test_coordinator_ignore_unknown_product_code(hass: HomeAssistant, mock_api_client):
    """Test coordinator ignores unknown product codes."""
    coordinator = PhynDataUpdateCoordinator(
        hass=hass,
        api_client=mock_api_client
    )
    
    # Add device with unknown product code
    coordinator.add_device("test-home-id", "test-device-id", "UNKNOWN")
    
    # Should not add any device
    assert len(coordinator.devices) == 0
