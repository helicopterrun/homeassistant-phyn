"""Test the Phyn entities."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.phyn.devices.pp import (
    PhynPlusDevice,
    PhynAutoShutoffModeSwitch,
    PhynAwayModeSwitch,
    PhynValve,
    PhynCurrentFlowRateSensor,
    PhynConsumptionSensor,
)
from custom_components.phyn.entities.base import (
    PhynDailyUsageSensor,
    PhynFirmwareUpdateAvailableSensor,
    PhynTemperatureSensor,
    PhynPressureSensor,
)


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = MagicMock()
    device.id = "test-device-id"
    device.home_id = "test-home-id"
    device.model = "PP1"
    device.manufacturer = "Phyn"
    device.firmware_version = "1.0.0"
    device.serial_number = "test-serial"
    device.device_name = "Phyn PP1"
    device.available = True
    device.coordinator = MagicMock()
    device.coordinator.api_client = MagicMock()
    device.coordinator.api_client.device = MagicMock()
    device.coordinator.api_client.device.open_valve = AsyncMock()
    device.coordinator.api_client.device.close_valve = AsyncMock()
    device.coordinator.async_add_listener = MagicMock(return_value=MagicMock())
    return device


async def test_daily_usage_sensor(mock_device):
    """Test daily usage sensor."""
    mock_device.consumption_today = 150.5
    
    sensor = PhynDailyUsageSensor(mock_device)
    
    assert sensor.unique_id == "test-device-id_daily_consumption"
    assert sensor.name == "Daily water usage"
    assert sensor.native_value == 150.5
    assert sensor.available is True


async def test_daily_usage_sensor_none_value(mock_device):
    """Test daily usage sensor with None value."""
    mock_device.consumption_today = None
    
    sensor = PhynDailyUsageSensor(mock_device)
    
    assert sensor.native_value is None


async def test_firmware_update_available_sensor(mock_device):
    """Test firmware update available sensor."""
    mock_device.firmware_has_update = True
    
    sensor = PhynFirmwareUpdateAvailableSensor(mock_device)
    
    assert sensor.unique_id == "test-device-id_firmware_update_available"
    assert sensor.is_on is True


async def test_firmware_update_not_available_sensor(mock_device):
    """Test firmware update not available sensor."""
    mock_device.firmware_has_update = False
    
    sensor = PhynFirmwareUpdateAvailableSensor(mock_device)
    
    assert sensor.is_on is False


async def test_temperature_sensor(mock_device):
    """Test temperature sensor."""
    mock_device.temperature = 72.5
    
    sensor = PhynTemperatureSensor(mock_device, "temperature", "Water Temperature")
    
    assert sensor.unique_id == "test-device-id_temperature"
    assert sensor.name == "Water Temperature"
    assert sensor.native_value == 72.5


async def test_temperature_sensor_with_device_property(mock_device):
    """Test temperature sensor with device property."""
    mock_device.temperature1 = 75.0
    
    sensor = PhynTemperatureSensor(mock_device, "temperature1", "Hot Water Temp", "temperature1")
    
    assert sensor.native_value == 75.0


async def test_pressure_sensor(mock_device):
    """Test pressure sensor."""
    mock_device.current_psi = 45.5
    
    sensor = PhynPressureSensor(mock_device, "pressure", "Water Pressure")
    
    assert sensor.unique_id == "test-device-id_pressure"
    assert sensor.name == "Water Pressure"
    assert sensor.native_value == 45.5


async def test_pressure_sensor_with_device_property(mock_device):
    """Test pressure sensor with device property."""
    mock_device.current_psi1 = 50.0
    
    sensor = PhynPressureSensor(mock_device, "pressure1", "Hot Water Pressure", "current_psi1")
    
    assert sensor.native_value == 50.0


async def test_current_flow_rate_sensor(mock_device):
    """Test current flow rate sensor."""
    mock_device.current_flow_rate = 2.456
    
    sensor = PhynCurrentFlowRateSensor(mock_device)
    
    assert sensor.unique_id == "test-device-id_current_flow_rate"
    assert sensor.native_value == 2.5  # Rounded to 1 decimal


async def test_current_flow_rate_sensor_zero(mock_device):
    """Test current flow rate sensor with zero value."""
    mock_device.current_flow_rate = 0.0
    
    sensor = PhynCurrentFlowRateSensor(mock_device)
    
    assert sensor.native_value == 0


async def test_consumption_sensor(mock_device):
    """Test consumption sensor."""
    mock_device.consumption = 123.45
    
    sensor = PhynConsumptionSensor(mock_device)
    
    assert sensor.unique_id == "test-device-id_consumption"
    assert sensor.native_value == 123.45


async def test_consumption_sensor_none(mock_device):
    """Test consumption sensor with None value."""
    mock_device.consumption = None
    
    sensor = PhynConsumptionSensor(mock_device)
    
    assert sensor.native_value is None


async def test_autoshutoff_switch(mock_device, hass: HomeAssistant):
    """Test autoshutoff switch."""
    mock_device.autoshutoff_enabled = True
    mock_device.set_autoshutoff_enabled = AsyncMock()
    
    switch = PhynAutoShutoffModeSwitch(mock_device)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()
    
    assert switch.unique_id == "test-device-id_autoshutoff_enabled"
    assert switch.is_on is True
    
    # Test turning off
    await switch.async_turn_off()
    mock_device.set_autoshutoff_enabled.assert_called_once_with(False)


async def test_autoshutoff_switch_turn_on(mock_device, hass: HomeAssistant):
    """Test autoshutoff switch turn on."""
    mock_device.autoshutoff_enabled = False
    mock_device.set_autoshutoff_enabled = AsyncMock()
    
    switch = PhynAutoShutoffModeSwitch(mock_device)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()
    
    assert switch.is_on is False
    
    # Test turning on
    await switch.async_turn_on()
    mock_device.set_autoshutoff_enabled.assert_called_once_with(True)


async def test_away_mode_switch(mock_device, hass: HomeAssistant):
    """Test away mode switch."""
    mock_device.away_mode = True
    mock_device.set_device_preference = AsyncMock()
    
    switch = PhynAwayModeSwitch(mock_device)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()
    
    assert switch.unique_id == "test-device-id_away_mode"
    assert switch.is_on is True
    
    # Test turning off
    await switch.async_turn_off()
    mock_device.set_device_preference.assert_called_once_with("leak_sensitivity_away_mode", "false")


async def test_away_mode_switch_turn_on(mock_device, hass: HomeAssistant):
    """Test away mode switch turn on."""
    mock_device.away_mode = False
    mock_device.set_device_preference = AsyncMock()
    
    switch = PhynAwayModeSwitch(mock_device)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()
    
    assert switch.is_on is False
    
    # Test turning on
    await switch.async_turn_on()
    mock_device.set_device_preference.assert_called_once_with("leak_sensitivity_away_mode", "true")


async def test_valve_open(mock_device):
    """Test valve entity in open state."""
    mock_device.valve_open = True
    mock_device.valve_changing = False
    
    valve = PhynValve(mock_device)
    
    assert valve.unique_id == "test-device-id_shutoff_valve"
    assert valve._attr_is_closed is False


async def test_valve_closed(mock_device):
    """Test valve entity in closed state."""
    mock_device.valve_open = False
    mock_device.valve_changing = False
    
    valve = PhynValve(mock_device)
    
    assert valve._attr_is_closed is True


async def test_valve_opening(mock_device):
    """Test valve entity opening."""
    mock_device.valve_open = False
    mock_device.valve_changing = True
    mock_device._last_known_valve_state = False
    
    valve = PhynValve(mock_device)
    
    assert valve._attr_is_opening is True
    assert valve._attr_is_closing is False


async def test_valve_closing(mock_device):
    """Test valve entity closing."""
    mock_device.valve_open = True
    mock_device.valve_changing = True
    mock_device._last_known_valve_state = True
    
    valve = PhynValve(mock_device)
    
    assert valve._attr_is_closing is True
    assert valve._attr_is_opening is False


async def test_valve_async_open(mock_device):
    """Test valve async open."""
    valve = PhynValve(mock_device)
    
    await valve.async_open_valve()
    
    mock_device.coordinator.api_client.device.open_valve.assert_called_once_with("test-device-id")


async def test_valve_async_close(mock_device):
    """Test valve async close."""
    valve = PhynValve(mock_device)
    
    await valve.async_close_valve()
    
    mock_device.coordinator.api_client.device.close_valve.assert_called_once_with("test-device-id")


async def test_entity_device_info(mock_device):
    """Test entity device info."""
    sensor = PhynDailyUsageSensor(mock_device)
    
    device_info = sensor.device_info
    
    assert device_info["identifiers"] == {("phyn", "test-device-id")}
    assert device_info["manufacturer"] == "Phyn"
    assert device_info["model"] == "PP1"
    assert device_info["sw_version"] == "1.0.0"
    assert device_info["serial_number"] == "test-serial"


async def test_entity_availability(mock_device):
    """Test entity availability."""
    mock_device.available = True
    sensor = PhynDailyUsageSensor(mock_device)
    assert sensor.available is True
    
    mock_device.available = False
    assert sensor.available is False
