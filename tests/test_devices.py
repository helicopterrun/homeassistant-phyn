"""Test the Phyn devices."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.phyn.devices.pp import PhynPlusDevice
from custom_components.phyn.devices.pc import PhynClassicDevice
from custom_components.phyn.devices.pw import PhynWaterSensorDevice


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.api_client = MagicMock()
    coordinator.api_client.device = MagicMock()
    coordinator.api_client.device.get_state = AsyncMock(return_value={
        "product_code": "PP1",
        "serial_number": "test-serial",
        "fw_version": "1.0.0",
        "online_status": {"v": "online"},
        "sov_status": {"v": "Open"},
        "flow": {"v": 1.5},
        "pressure": {"v": 45.5},
        "temperature": {"v": 72.0},
        "flow_state": {"v": 0.0, "ts": 0},
    })
    coordinator.api_client.device.get_autoshuftoff_status = AsyncMock(return_value={
        "auto_shutoff_enable": True
    })
    coordinator.api_client.device.get_device_preferences = AsyncMock(return_value=[
        {"name": "leak_sensitivity_away_mode", "value": "false"},
        {"name": "scheduler_enable", "value": "true"}
    ])
    coordinator.api_client.device.get_consumption = AsyncMock(return_value={
        "water_consumption": 150.5
    })
    coordinator.api_client.device.get_health_tests = AsyncMock(return_value={
        "data": []
    })
    coordinator.api_client.device.get_latest_firmware_info = AsyncMock(return_value=[{
        "fw_version": "2.0.0",
        "release_notes": "http://example.com/release-notes"
    }])
    coordinator.api_client.mqtt = MagicMock()
    coordinator.api_client.mqtt.add_event_handler = AsyncMock()
    coordinator.api_client.mqtt.subscribe = AsyncMock()
    return coordinator


async def test_phyn_plus_device_initialization(mock_coordinator):
    """Test PhynPlusDevice initialization."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    assert device.id == "test-device-id"
    assert device.home_id == "test-home-id"
    assert device.model == ""  # Not set until state is updated
    assert device.manufacturer == "Phyn"
    assert len(device.entities) == 15  # Check all entities are created


async def test_phyn_plus_device_setup(mock_coordinator):
    """Test PhynPlusDevice setup."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    # Initialize device state with required keys
    device._device_state["sov_status"] = {"v": "Open"}
    
    result = await device.async_setup()
    
    # Verify MQTT event handler was added
    mock_coordinator.api_client.mqtt.add_event_handler.assert_called_once()
    # Verify MQTT subscription was made
    mock_coordinator.api_client.mqtt.subscribe.assert_called_once_with(
        "prd/app_subscriptions/test-device-id"
    )
    # Verify return value
    assert result == "Open"


async def test_phyn_plus_device_update_data(mock_coordinator):
    """Test PhynPlusDevice data update."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    await device.async_update_data()
    
    # Verify all API calls were made
    mock_coordinator.api_client.device.get_state.assert_called_once()
    mock_coordinator.api_client.device.get_autoshuftoff_status.assert_called_once()
    mock_coordinator.api_client.device.get_device_preferences.assert_called_once()
    mock_coordinator.api_client.device.get_consumption.assert_called_once()


async def test_phyn_plus_device_properties(mock_coordinator):
    """Test PhynPlusDevice properties."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    await device.async_update_data()
    
    assert device.current_flow_rate == 1.5
    assert device.current_psi == 45.5
    assert device.temperature == 72.0
    assert device.valve_open is True
    assert device.autoshutoff_enabled is True
    assert device.scheduled_leak_test_enabled is True


async def test_phyn_plus_device_unavailable(mock_coordinator):
    """Test PhynPlusDevice unavailable state."""
    mock_coordinator.api_client.device.get_state = AsyncMock(return_value={
        "online_status": {"v": "offline"}
    })
    
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    await device.async_update_data()
    
    assert device.available is False


async def test_phyn_plus_device_real_time_update(mock_coordinator):
    """Test PhynPlusDevice real-time MQTT updates."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    # Mock entities
    for entity in device.entities:
        entity.async_write_ha_state = MagicMock()
    
    # Simulate MQTT update
    update_data = {
        "consumption": {"v": 123.45},
        "flow": {"v": 2.5},
        "sov_state": "Partial",
        "sensor_data": {
            "pressure": {"v": 50.0},
            "temperature": {"v": 75.0}
        }
    }
    
    await device.on_device_update("test-device-id", update_data)
    
    # Verify state was updated
    assert device._device_state["consumption"] == 123.45
    assert device._device_state["flow"]["v"] == 2.5
    assert device._device_state["sov_status"]["v"] == "Partial"
    assert device._device_state["pressure"]["v"] == 50.0
    assert device._device_state["temperature"]["v"] == 75.0
    
    # Verify entities were updated
    for entity in device.entities:
        entity.async_write_ha_state.assert_called_once()


async def test_phyn_classic_device_initialization(mock_coordinator):
    """Test PhynClassicDevice initialization."""
    device = PhynClassicDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PC1"
    )
    
    assert device.id == "test-device-id"
    assert device.home_id == "test-home-id"
    assert device.manufacturer == "Phyn"
    assert len(device.entities) == 7  # Check all entities are created


async def test_phyn_classic_device_update_data(mock_coordinator):
    """Test PhynClassicDevice data update."""
    device = PhynClassicDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PC1"
    )
    
    await device.async_update_data()
    
    # Verify API calls were made
    mock_coordinator.api_client.device.get_state.assert_called()
    mock_coordinator.api_client.device.get_consumption.assert_called_once()


async def test_phyn_water_sensor_device_initialization(mock_coordinator):
    """Test PhynWaterSensorDevice initialization."""
    mock_coordinator.api_client.device.get_state = AsyncMock(return_value={
        "name": "Basement Sensor",
        "product_code": "PW1",
        "serial_number": "test-serial",
        "fw_version": "1.0.0",
        "online_status": {"v": "online"}
    })
    
    device = PhynWaterSensorDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PW1"
    )
    
    assert device.id == "test-device-id"
    assert device.home_id == "test-home-id"
    assert device.manufacturer == "Phyn"
    assert len(device.entities) == 8  # Check all entities are created


async def test_phyn_water_sensor_device_update_data(mock_coordinator):
    """Test PhynWaterSensorDevice data update."""
    # Mock get_water_statistics to return array of entries with timestamps
    mock_coordinator.api_client.device.get_water_statistics = AsyncMock(return_value=[
        {
            "ts": 1000,
            "battery_level": 85,
            "humidity": [{"value": 65.5}],
            "temperature": [{"value": 68.0}],
            "alerts": {
                "high_humidity": False,
                "low_humidity": False,
                "low_temperature": False,
                "water": True
            }
        }
    ])
    
    device = PhynWaterSensorDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PW1"
    )
    
    await device.async_update_data()
    
    # Verify API calls were made
    mock_coordinator.api_client.device.get_state.assert_called()
    mock_coordinator.api_client.device.get_water_statistics.assert_called_once()


async def test_phyn_water_sensor_device_properties(mock_coordinator):
    """Test PhynWaterSensorDevice properties."""
    mock_coordinator.api_client.device.get_water_statistics = AsyncMock(return_value=[
        {
            "ts": 1000,
            "battery_level": 85,
            "humidity": [{"value": 65.5}],
            "temperature": [{"value": 68.0}],
            "alerts": {
                "high_humidity": True,
                "low_humidity": False,
                "low_temperature": False,
                "water": True
            }
        }
    ])
    
    device = PhynWaterSensorDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PW1"
    )
    
    await device.async_update_data()
    
    assert device.battery == 85
    assert device.humidity == 65.5
    assert device.temperature == 68.0
    assert device.high_humidity is True
    assert device.low_humidity is False
    assert device.low_temperature is False
    assert device.water_detected is True


async def test_device_firmware_has_update(mock_coordinator):
    """Test device firmware update detection."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    # Set current firmware version
    device._device_state["fw_version"] = "100"
    
    # Mock firmware info to return numeric version
    mock_coordinator.api_client.device.get_latest_firmware_info = AsyncMock(return_value=[{
        "fw_version": "200",
        "release_notes": "http://example.com/release-notes"
    }])
    
    # Update firmware info
    await device._update_firmware_information()
    
    # Check that update is detected (200 > 100)
    assert device.firmware_has_update is True
    assert device.firmware_latest_version == "200"
    assert device.firmware_release_url == "http://example.com/release-notes"
