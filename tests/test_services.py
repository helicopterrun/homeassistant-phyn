"""Test the Phyn services."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.phyn.const import DOMAIN, CLIENT
from custom_components.phyn.services import phyn_leak_test, phyn_leak_test_service_setup


@pytest.fixture
async def setup_phyn(hass: HomeAssistant):
    """Set up Phyn integration."""
    # Mock client
    mock_client = MagicMock()
    mock_client.device = MagicMock()
    mock_client.device.run_leak_test = AsyncMock(return_value={
        "code": "success"
    })
    
    hass.data[DOMAIN] = {CLIENT: mock_client}
    
    # Set up device and entity registries
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    
    # Create a proper config entry
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test")
    config_entry.add_to_hass(hass)
    
    # Create a device
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test-device-id")},
        name="Test Phyn Device",
    )
    
    # Create an entity
    entity_registry.async_get_or_create(
        "valve",
        DOMAIN,
        "test-device-id_shutoff_valve",
        suggested_object_id="test_valve",
        device_id=device.id,
    )
    
    return mock_client


async def test_leak_test_service(hass: HomeAssistant, setup_phyn):
    """Test the leak test service."""
    mock_client = setup_phyn
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="leak_test",
        data={
            "entity_id": "valve.test_valve"
        },
        hass=hass,
    )
    
    # Call the service
    await phyn_leak_test(service_call)
    
    # Verify the API was called
    mock_client.device.run_leak_test.assert_called_once()
    args = mock_client.device.run_leak_test.call_args
    assert args[0][0] == "test-device-id"
    assert args[0][1] == "false"  # extended=False by default


async def test_leak_test_service_extended(hass: HomeAssistant, setup_phyn):
    """Test the leak test service with extended test."""
    mock_client = setup_phyn
    
    # Create service call with extended parameter
    service_call = ServiceCall(
        domain=DOMAIN,
        service="leak_test",
        data={
            "entity_id": "valve.test_valve",
            "extended": True
        },
        hass=hass,
    )
    
    # Call the service
    await phyn_leak_test(service_call)
    
    # Verify the API was called with extended=true
    mock_client.device.run_leak_test.assert_called_once()
    args = mock_client.device.run_leak_test.call_args
    assert args[0][0] == "test-device-id"
    assert args[0][1] == "true"


async def test_leak_test_service_error(hass: HomeAssistant, setup_phyn):
    """Test the leak test service with error response."""
    mock_client = setup_phyn
    
    # Mock error response
    mock_client.device.run_leak_test = AsyncMock(return_value={
        "code": "error",
        "message": "Test failed"
    })
    
    # Create service call
    service_call = ServiceCall(
        domain=DOMAIN,
        service="leak_test",
        data={
            "entity_id": "valve.test_valve"
        },
        hass=hass,
    )
    
    # Call the service and expect assertion error
    with pytest.raises(AssertionError):
        await phyn_leak_test(service_call)


async def test_leak_test_service_setup(hass: HomeAssistant):
    """Test the leak test service setup."""
    await phyn_leak_test_service_setup(hass)
    
    # Verify service is registered
    assert hass.services.has_service(DOMAIN, "leak_test")


async def test_leak_test_service_device_not_found(hass: HomeAssistant):
    """Test leak test service with non-existent device."""
    # Setup without proper device/entity
    hass.data[DOMAIN] = {CLIENT: MagicMock()}
    
    service_call = ServiceCall(
        domain=DOMAIN,
        service="leak_test",
        data={
            "entity_id": "valve.nonexistent"
        },
        hass=hass,
    )
    
    # Should raise an error when entity doesn't exist
    with pytest.raises((KeyError, ValueError, AttributeError)):
        await phyn_leak_test(service_call)
