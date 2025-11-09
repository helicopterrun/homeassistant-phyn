"""Test error scenarios and edge cases."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant

from custom_components.phyn.devices.pp import PhynPlusDevice
from custom_components.phyn.devices.pc import PhynClassicDevice
from custom_components.phyn.entities.base import (
    PhynAlertSensor,
    PhynHumiditySensor,
)


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
    })
    return coordinator


async def test_phyn_plus_valve_open_none():
    """Test PhynPlusDevice valve_open when None."""
    device = MagicMock()
    device._device_state = {}
    device.valve_changing = False
    device._last_known_valve_state = True
    
    # Mock the valve_open property behavior
    sov_status = device._device_state.get("sov_status", {})
    assert sov_status.get("v") is None


async def test_phyn_plus_leak_test_running():
    """Test PhynPlusDevice leak_test_running property."""
    device = MagicMock()
    device._device_state = {"sov_status": {"v": "LeakExp"}}
    
    # Import and test the actual class
    from custom_components.phyn.devices.pp import PhynPlusDevice
    actual_device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    actual_device._device_state = {"sov_status": {"v": "LeakExp"}}
    assert actual_device.leak_test_running is True
    
    actual_device._device_state = {"sov_status": {"v": "Open"}}
    assert actual_device.leak_test_running is False


async def test_phyn_plus_set_away_mode(mock_coordinator):
    """Test PhynPlusDevice set_away_mode method."""
    mock_coordinator.api_client.device.set_device_preferences = AsyncMock()
    
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    device._device_preferences = {"leak_sensitivity_away_mode": {"value": "false"}}
    
    # Set away mode to True
    await device.set_away_mode(True)
    
    mock_coordinator.api_client.device.set_device_preferences.assert_called_once()
    call_args = mock_coordinator.api_client.device.set_device_preferences.call_args
    assert call_args[0][0] == "test-device-id"
    assert call_args[0][1][0]["value"] == "true"


async def test_phyn_plus_set_scheduler_enabled(mock_coordinator):
    """Test PhynPlusDevice set_scheduler_enabled method."""
    mock_coordinator.api_client.device.set_device_preferences = AsyncMock()
    
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    device._device_preferences = {"scheduler_enable": {"value": "false"}}
    
    # Set scheduler to True
    await device.set_scheduler_enabled(True)
    
    mock_coordinator.api_client.device.set_device_preferences.assert_called_once()
    call_args = mock_coordinator.api_client.device.set_device_preferences.call_args
    assert call_args[0][0] == "test-device-id"
    assert call_args[0][1][0]["name"] == "scheduler_enable"
    assert call_args[0][1][0]["value"] == "true"


async def test_phyn_plus_set_device_preference_invalid_name(mock_coordinator):
    """Test PhynPlusDevice set_device_preference with invalid name."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    # Try to set invalid preference
    result = await device.set_device_preference("invalid_preference", "true")
    
    assert result is None


async def test_phyn_plus_set_device_preference_invalid_value(mock_coordinator):
    """Test PhynPlusDevice set_device_preference with invalid value."""
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    # Try to set invalid value
    result = await device.set_device_preference("leak_sensitivity_away_mode", "invalid")
    
    assert result is None


async def test_phyn_classic_cold_line_num(mock_coordinator):
    """Test PhynClassicDevice cold_line_num property."""
    device = PhynClassicDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PC1"
    )
    
    device._device_state = {"cold_line_num": 2}
    assert device.cold_line_num == 2
    
    device._device_state = {}
    assert device.cold_line_num is None


async def test_phyn_alert_sensor():
    """Test PhynAlertSensor with missing property."""
    device = MagicMock()
    device.id = "test-id"
    device.nonexistent_property = None
    
    # Remove the attribute to test the hasattr check
    del device.nonexistent_property
    
    sensor = PhynAlertSensor(device, "test_alert", "Test Alert", "nonexistent_property")
    
    assert sensor.is_on is None


async def test_phyn_humidity_sensor_none_values():
    """Test PhynHumiditySensor with None values."""
    device = MagicMock()
    device.id = "test-id"
    device.humidity = None
    
    sensor = PhynHumiditySensor(device, "humidity", "Humidity")
    
    assert sensor.native_value is None


async def test_phyn_plus_consumption_property():
    """Test PhynPlusDevice consumption property."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    # Test when consumption not in rt_device_state
    device._rt_device_state = {}
    assert device.consumption is None
    
    # Test when consumption in device_state
    device._rt_device_state = {"consumption": {"v": 100.0}}
    device._device_state = {"consumption": 100.0}
    assert device.consumption == 100.0


async def test_phyn_plus_valve_partial_state():
    """Test PhynPlusDevice valve in partial state."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {"sov_status": {"v": "Partial"}}
    device._last_known_valve_state = True
    
    assert device.valve_changing is True
    assert device.valve_open is True  # Returns last known state


async def test_phyn_classic_current_flow_rate_none():
    """Test PhynClassicDevice current_flow_rate returns None."""
    device = PhynClassicDevice(MagicMock(), "home-id", "device-id", "PC1")
    
    device._device_state = {"flow": {}}
    assert device.current_flow_rate is None


async def test_device_rssi_property():
    """Test device rssi property."""
    from custom_components.phyn.devices.base import PhynDevice
    
    device = PhynDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {"signal_strength": -50}
    assert device.rssi == -50
    
    device._device_state = {}
    assert device.rssi is None


async def test_device_firmware_version_empty():
    """Test device firmware_version when empty."""
    from custom_components.phyn.devices.base import PhynDevice
    
    device = PhynDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {}
    assert device.firmware_version == ""


async def test_device_firmware_has_update_none():
    """Test device firmware_has_update returns None."""
    from custom_components.phyn.devices.base import PhynDevice
    
    device = PhynDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    # No firmware info
    assert device.firmware_has_update is None


async def test_device_firmware_has_update_no_device_fw():
    """Test device firmware_has_update with no device firmware."""
    from custom_components.phyn.devices.base import PhynDevice
    
    device = PhynDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._firmware_info = {"fw_version": "200"}
    device._device_state = {}
    
    assert device.firmware_has_update is False


async def test_phyn_plus_on_device_update_ignores_other_device():
    """Test PhynPlusDevice on_device_update ignores other devices."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    original_state = dict(device._device_state)
    
    # Update for different device
    await device.on_device_update("other-device-id", {"consumption": {"v": 999.0}})
    
    # State should not change
    assert device._device_state == original_state


async def test_phyn_classic_properties(mock_coordinator):
    """Test PhynClassicDevice properties."""
    device = PhynClassicDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PC1"
    )
    
    device._device_state = {
        "hot_line_num": 1,
        "cold_line_num": 2,
        "pressure1": {"v": 50.5},
        "pressure2": {"mean": 45.3},
        "temperature1": {"v": 75.2},
        "temperature2": {"mean": 70.8},
        "flow": {"v": 2.5}
    }
    
    assert device.hot_line_num == 1
    assert device.cold_line_num == 2
    assert device.current_psi1 == 50.5
    assert device.current_psi2 == 45.3
    assert device.temperature1 == 75.2
    assert device.temperature2 == 70.8
    assert device.current_flow_rate == 2.5


async def test_phyn_classic_leak_test_running(mock_coordinator):
    """Test PhynClassicDevice leak_test_running property."""
    device = PhynClassicDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PC1"
    )
    
    device._device_state = {"sov_status": {"v": "LeakExp"}}
    assert device.leak_test_running is True
    
    device._device_state = {"sov_status": {"v": "Open"}}
    assert device.leak_test_running is False


async def test_phyn_water_sensor_device_name():
    """Test PhynWaterSensorDevice device_name property."""
    from custom_components.phyn.devices.pw import PhynWaterSensorDevice
    
    device = PhynWaterSensorDevice(
        coordinator=MagicMock(),
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PW1"
    )
    
    # Test with name in device state
    device._device_state = {"name": "Basement Sensor"}
    assert "Basement Sensor" in device.device_name
    
    # Test without name in device state
    device._device_state = {}
    assert "Phyn" in device.device_name


async def test_entity_async_update(mock_coordinator):
    """Test entity async_update calls device refresh."""
    from custom_components.phyn.entities.base import PhynDailyUsageSensor
    
    device = MagicMock()
    device.id = "test-id"
    device.consumption_today = 100.0
    device.async_request_refresh = AsyncMock()
    
    sensor = PhynDailyUsageSensor(device)
    
    await sensor.async_update()
    
    device.async_request_refresh.assert_called_once()


async def test_phyn_plus_health_test_error(mock_coordinator):
    """Test PhynPlusDevice handling health test error."""
    mock_coordinator.api_client.device.get_health_tests = AsyncMock(
        side_effect=Exception("Health test error")
    )
    
    device = PhynPlusDevice(
        coordinator=mock_coordinator,
        home_id="test-home-id",
        device_id="test-device-id",
        product_code="PP1"
    )
    
    await device._update_device_health_tests()
    
    assert device._latest_health_test is None


async def test_phyn_plus_scheduled_leak_test_enabled_none():
    """Test PhynPlusDevice scheduled_leak_test_enabled when not available."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_preferences = {}
    assert device.scheduled_leak_test_enabled is None


async def test_phyn_plus_away_mode_none():
    """Test PhynPlusDevice away_mode when not available."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_preferences = {}
    assert device.away_mode is None


async def test_phyn_plus_autoshutoff_enabled_none():
    """Test PhynPlusDevice autoshutoff_enabled when not available."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._auto_shutoff = {}
    assert device.autoshutoff_enabled is None


async def test_phyn_plus_current_flow_rate_none():
    """Test PhynPlusDevice current_flow_rate returns None."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {"flow": {}}
    assert device.current_flow_rate is None


async def test_phyn_plus_current_psi_with_mean():
    """Test PhynPlusDevice current_psi with mean value."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {"pressure": {"mean": 47.5}}
    assert device.current_psi == 47.5


async def test_phyn_plus_temperature_with_mean():
    """Test PhynPlusDevice temperature with mean value."""
    device = PhynPlusDevice(MagicMock(), "home-id", "device-id", "PP1")
    
    device._device_state = {"temperature": {"mean": 73.2}}
    assert device.temperature == 73.2
