"""Test Phyn platform setup."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.valve import ValveEntity
from homeassistant.components.update import UpdateEntity
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.phyn.const import DOMAIN
from custom_components.phyn import binary_sensor, sensor, switch, valve, update
from custom_components.phyn.devices.pp import PhynPlusDevice


@pytest.fixture
def mock_coordinator_with_device():
    """Create a mock coordinator with a device."""
    coordinator = MagicMock()
    
    # Create a mock device with entities
    device = MagicMock(spec=PhynPlusDevice)
    
    # Create mock entities
    mock_binary_sensor = MagicMock(spec=BinarySensorEntity)
    mock_sensor = MagicMock(spec=SensorEntity)
    mock_switch = MagicMock(spec=SwitchEntity)
    mock_valve = MagicMock(spec=ValveEntity)
    mock_update = MagicMock(spec=UpdateEntity)
    
    device.entities = [
        mock_binary_sensor,
        mock_sensor,
        mock_switch,
        mock_valve,
        mock_update,
    ]
    
    coordinator.devices = [device]
    
    return coordinator


async def test_binary_sensor_async_setup_entry(hass: HomeAssistant, mock_coordinator_with_device):
    """Test binary sensor platform setup."""
    hass.data[DOMAIN] = {"coordinator": mock_coordinator_with_device}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    
    async_add_entities = MagicMock()
    
    await binary_sensor.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], BinarySensorEntity)


async def test_sensor_async_setup_entry(hass: HomeAssistant, mock_coordinator_with_device):
    """Test sensor platform setup."""
    hass.data[DOMAIN] = {"coordinator": mock_coordinator_with_device}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    
    async_add_entities = MagicMock()
    
    await sensor.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], SensorEntity)


async def test_switch_async_setup_entry(hass: HomeAssistant, mock_coordinator_with_device):
    """Test switch platform setup."""
    hass.data[DOMAIN] = {"coordinator": mock_coordinator_with_device}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    
    async_add_entities = MagicMock()
    
    await switch.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], SwitchEntity)


async def test_valve_async_setup_entry(hass: HomeAssistant, mock_coordinator_with_device):
    """Test valve platform setup."""
    hass.data[DOMAIN] = {"coordinator": mock_coordinator_with_device}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    
    async_add_entities = MagicMock()
    
    await valve.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], ValveEntity)


async def test_update_async_setup_entry(hass: HomeAssistant, mock_coordinator_with_device):
    """Test update platform setup."""
    hass.data[DOMAIN] = {"coordinator": mock_coordinator_with_device}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    
    async_add_entities = MagicMock()
    
    await update.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], UpdateEntity)


async def test_binary_sensor_multiple_devices(hass: HomeAssistant):
    """Test binary sensor platform with multiple devices."""
    coordinator = MagicMock()
    
    # Create multiple devices with binary sensors
    device1 = MagicMock()
    device1.entities = [MagicMock(spec=BinarySensorEntity), MagicMock(spec=SensorEntity)]
    
    device2 = MagicMock()
    device2.entities = [MagicMock(spec=BinarySensorEntity)]
    
    coordinator.devices = [device1, device2]
    
    hass.data[DOMAIN] = {"coordinator": coordinator}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    async_add_entities = MagicMock()
    
    await binary_sensor.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify only binary sensors were added
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2  # 2 binary sensors from 2 devices


async def test_sensor_no_entities(hass: HomeAssistant):
    """Test sensor platform when no sensor entities exist."""
    coordinator = MagicMock()
    
    # Create device with no sensor entities
    device = MagicMock()
    device.entities = [MagicMock(spec=BinarySensorEntity)]
    
    coordinator.devices = [device]
    
    hass.data[DOMAIN] = {"coordinator": coordinator}
    
    config_entry = MockConfigEntry(domain=DOMAIN)
    async_add_entities = MagicMock()
    
    await sensor.async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify empty list was passed
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 0
