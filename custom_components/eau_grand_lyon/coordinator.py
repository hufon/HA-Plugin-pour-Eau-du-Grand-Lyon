"""Coordinateur de mise à jour pour Eau du Grand Lyon."""
from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EauGrandLyonApi, AuthenticationError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class EauGrandLyonCoordinator(DataUpdateCoordinator[dict]):
    """Gère les mises à jour périodiques des données Eau du Grand Lyon.

    Structure de coordinator.data :
    {
        "contracts": {
            "<reference>": {
                "id":                  str,   # AEL session ID (pour les appels API)
                "reference":           str,   # ex. "1703106"
                "statut":              str,   # ex. "actif"
                "date_effet":          str,   # "YYYY-MM-DD"
                "date_echeance":       str,   # "YYYY-MM-DD"
                "solde_eur":           float, # solde du compte client (€)
                "mensualise":          bool,
                "mode_paiement":       str,
                "calibre_compteur":    str,   # ex. "15"
                "usage":               str,   # ex. "eau domestique"
                "nombre_habitants":    str,   # ex. "5"
                "reference_pds":       str,   # référence PDS/EDS
                "consommations":       list,  # [{mois, annee, label, consommation_m3}, ...]
                "consommation_mois_courant":  float | None,
                "label_mois_courant":        str | None,
                "consommation_mois_precedent": float | None,
                "label_mois_precedent":      str | None,
                "consommation_annuelle":     float,  # somme des 12 derniers mois
            },
            ...
        },
        "nb_alertes": int,
    }
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        self._entry = entry
        # Session dédiée avec CookieJar(unsafe=True) — garantit que le cookie HttpOnly
        # du login est bien stocké et renvoyé lors du flux OAuth2 PKCE, sans
        # interférence avec les autres intégrations qui partagent la session HA.
        self._own_session = aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(unsafe=True)
        )
        self.api = EauGrandLyonApi(
            self._own_session,
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )

    async def async_close(self) -> None:
        """Ferme la session aiohttp dédiée."""
        if not self._own_session.closed:
            await self._own_session.close()

    async def _async_update_data(self) -> dict:
        """Récupère toutes les données depuis l'API."""
        try:
            # Ré-authentification systématique à chaque rafraîchissement
            await self.api.authenticate()

            # 1. Contrats avec détails (référence, solde, service, etc.)
            raw_contracts = await self.api.get_contracts()
            _LOGGER.debug("%d contrat(s) trouvé(s)", len(raw_contracts))

            # 2. Alertes actives (tous contrats)
            alertes = await self.api.get_alertes()

            # 3. Consommations par contrat
            contracts_data: dict[str, dict] = {}
            for raw in raw_contracts:
                details = EauGrandLyonApi.parse_contract_details(raw)
                ref = details["reference"]
                if not ref:
                    continue

                cid = details["id"]
                raw_consos = await self.api.get_monthly_consumptions(cid)
                consos = EauGrandLyonApi.format_consumptions(raw_consos)

                # Valeurs dérivées
                conso_courant = consos[-1]["consommation_m3"] if consos else None
                label_courant = consos[-1]["label"] if consos else None
                conso_precedent = consos[-2]["consommation_m3"] if len(consos) >= 2 else None
                label_precedent = consos[-2]["label"] if len(consos) >= 2 else None
                # Somme glissante des 12 derniers mois
                last_12 = consos[-12:] if len(consos) >= 12 else consos
                conso_annuelle = round(sum(e["consommation_m3"] for e in last_12), 1)

                contracts_data[ref] = {
                    **details,
                    "consommations": consos,
                    "consommation_mois_courant": conso_courant,
                    "label_mois_courant": label_courant,
                    "consommation_mois_precedent": conso_precedent,
                    "label_mois_precedent": label_precedent,
                    "consommation_annuelle": conso_annuelle,
                }
                _LOGGER.debug(
                    "Contrat %s : %d mois, conso courante=%.1f m³, annuelle=%.1f m³",
                    ref, len(consos),
                    conso_courant or 0,
                    conso_annuelle,
                )

            return {
                "contracts": contracts_data,
                "nb_alertes": len(alertes),
            }

        except AuthenticationError as err:
            raise UpdateFailed(f"Erreur d'authentification: {err}") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Erreur lors de la récupération des données: {err}") from err
