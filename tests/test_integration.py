"""Test Phyn integration end-to-end."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.phyn.const import DOMAIN


@pytest.fixture
def mock_full_api():
    """Create a full mock API for integration tests."""
    with patch("aiophyn.async_get_api", new=AsyncMock()) as mock_api:
        mock_api_instance = MagicMock()
        
        # Mock home data
        mock_api_instance.home.get_homes = AsyncMock(return_value=[
            {
                "id": "test-home-id",
                "alias_name": "Test Home",
                "devices": [
                    {
                        "device_id": "test-pp-device",
                        "product_code": "PP1",
                    },
                    {
                        "device_id": "test-pc-device",
                        "product_code": "PC1",
                    },
                    {
                        "device_id": "test-pw-device",
                        "product_code": "PW1",
                    }
                ],
            }
        ])
        
        # Mock device state
        mock_api_instance.device.get_state = AsyncMock(return_value={
            "product_code": "PP1",
            "serial_number": "test-serial",
            "fw_version": "1.0.0",
            "online_status": {"v": "online"},
            "sov_status": {"v": "Open"},
            "flow": {"v": 1.5},
            "pressure": {"v": 45.5},
            "temperature": {"v": 72.0},
        })
        
        # Mock other API calls
        mock_api_instance.device.get_autoshuftoff_status = AsyncMock(return_value={
            "auto_shutoff_enable": True
        })
        mock_api_instance.device.get_device_preferences = AsyncMock(return_value=[
            {"name": "leak_sensitivity_away_mode", "value": "false"},
            {"name": "scheduler_enable", "value": "true"}
        ])
        mock_api_instance.device.get_consumption = AsyncMock(return_value={
            "water_consumption": 150.5
        })
        mock_api_instance.device.get_health_tests = AsyncMock(return_value={
            "data": []
        })
        mock_api_instance.device.get_latest_firmware_info = AsyncMock(return_value=[{
            "fw_version": "2.0.0",
            "release_notes": "http://example.com/release-notes"
        }])
        mock_api_instance.device.get_water_statistics = AsyncMock(return_value={
            "battery_level": 85,
            "humidity": [{"value": 65.5}],
            "temperature": [{"value": 68.0}],
            "alerts": {}
        })
        
        # Mock MQTT
        mock_api_instance.mqtt.connect = AsyncMock()
        mock_api_instance.mqtt.disconnect_and_wait = AsyncMock()
        mock_api_instance.mqtt.add_event_handler = AsyncMock()
        mock_api_instance.mqtt.subscribe = AsyncMock()
        
        mock_api.return_value = mock_api_instance
        
        yield mock_api


async def test_full_integration_setup(hass: HomeAssistant, mock_full_api):
    """Test full integration setup with multiple devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    # Setup integration
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        mock_coordinator_instance.async_refresh = AsyncMock()
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup", new=AsyncMock()):
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()
    
    # Verify entry is loaded
    assert entry.state == ConfigEntryState.LOADED
    
    # Verify all devices were added
    assert mock_coordinator_instance.add_device.call_count == 3


async def test_integration_setup_and_unload(hass: HomeAssistant, mock_full_api):
    """Test integration setup and unload cycle."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    # Setup
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        mock_coordinator_instance.async_refresh = AsyncMock()
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup", new=AsyncMock()):
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()
    
    assert entry.state == ConfigEntryState.LOADED
    
    # Unload
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    
    assert entry.state == ConfigEntryState.NOT_LOADED
    
    # Verify MQTT was disconnected
    mock_full_api.return_value.mqtt.disconnect_and_wait.assert_called()


async def test_integration_mqtt_disconnect_on_setup_error(hass: HomeAssistant, mock_full_api):
    """Test MQTT disconnects on setup error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    # Setup with error after MQTT connect
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        # Make async_refresh raise an error
        mock_coordinator_instance.async_refresh = AsyncMock(side_effect=Exception("Setup failed"))
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup", new=AsyncMock()):
            # Setup should fail
            assert not await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()
    
    # Verify MQTT was disconnected after error
    mock_full_api.return_value.mqtt.disconnect_and_wait.assert_called()


async def test_integration_platforms_loaded(hass: HomeAssistant, mock_full_api):
    """Test all platforms are loaded during setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        mock_coordinator_instance.async_refresh = AsyncMock()
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup", new=AsyncMock()):
            with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
                assert await async_setup_component(hass, DOMAIN, {})
                await hass.async_block_till_done()
                
                # Verify all platforms were forwarded
                mock_forward.assert_called_once()
                platforms = mock_forward.call_args[0][1]
                assert len(platforms) == 5  # binary_sensor, sensor, switch, update, valve


async def test_integration_service_registered(hass: HomeAssistant, mock_full_api):
    """Test leak test service is registered during setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        mock_coordinator_instance.async_refresh = AsyncMock()
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup") as mock_service_setup:
            mock_service_setup.return_value = AsyncMock()
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()
            
            # Verify service setup was called
            mock_service_setup.assert_called_once_with(hass)


async def test_integration_coordinator_refresh_called(hass: HomeAssistant, mock_full_api):
    """Test coordinator refresh is called during setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
            "Brand": "Phyn",
        },
        unique_id="test@example.com",
    )
    entry.add_to_hass(hass)
    
    with patch("custom_components.phyn.PhynDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.devices = []
        mock_coordinator_instance.add_device = MagicMock()
        mock_coordinator_instance.async_refresh = AsyncMock()
        mock_coordinator_instance.async_setup = AsyncMock()
        mock_coordinator.return_value = mock_coordinator_instance
        
        with patch("custom_components.phyn.phyn_leak_test_service_setup", new=AsyncMock()):
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()
            
            # Verify coordinator refresh was called
            mock_coordinator_instance.async_refresh.assert_called_once()
            mock_coordinator_instance.async_setup.assert_called_once()
