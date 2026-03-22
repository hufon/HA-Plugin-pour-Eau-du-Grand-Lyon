"""Binary sensors pour Eau du Grand Lyon."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EauGrandLyonCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée les binary sensors Eau du Grand Lyon."""
    coordinator: EauGrandLyonCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EauGrandLyonLeakAlertSensor(coordinator, entry, ref)
        for ref in (coordinator.data or {}).get("contracts", {})
    ]
    async_add_entities(entities, update_before_add=True)


class EauGrandLyonLeakAlertSensor(
    CoordinatorEntity[EauGrandLyonCoordinator], BinarySensorEntity
):
    """Alerte possible fuite basée sur surconsommation mensuelle."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Alerte fuite possible"

    def __init__(
        self,
        coordinator: EauGrandLyonCoordinator,
        entry: ConfigEntry,
        contract_ref: str,
    ) -> None:
        super().__init__(coordinator)
        self._contract_ref = contract_ref
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{contract_ref}_leak_alert"

    @property
    def _contract(self) -> dict:
        if not self.coordinator.data:
            return {}
        return self.coordinator.data.get("contracts", {}).get(self._contract_ref, {})

    @property
    def device_info(self) -> DeviceInfo:
        calibre = self._contract.get("calibre_compteur", "")
        usage = self._contract.get("usage", "")
        model_parts = [p for p in [calibre and f"DN{calibre}", usage] if p]
        numero_compteur = (
            self._contract.get("reference_pds")
            or self._contract.get("reference", self._contract_ref)
        )
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_{self._contract_ref}")},
            name="Eau du Grand Lyon",
            manufacturer="Morgeek",
            model=", ".join(model_parts) or "Compteur eau",
            serial_number=numero_compteur,
            configuration_url="https://agence.eaudugrandlyon.com",
        )

    @property
    def is_on(self) -> bool:
        c = self._contract
        conso_courant = c.get("consommation_mois_courant")
        conso_precedent = c.get("consommation_mois_precedent")
        if conso_courant and conso_precedent:
            return conso_courant > 2 * conso_precedent
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        c = self._contract
        return {
            "consommation_courant_m3": c.get("consommation_mois_courant"),
            "consommation_precedent_m3": c.get("consommation_mois_precedent"),
            "seuil_alerte": "Consommation actuelle > 2x précédente",
        }
