"""Config flow pour l'intégration Eau du Grand Lyon."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries

from .api import AuthenticationError, EauGrandLyonApi
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class EauGrandLyonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration de l'intégration Eau du Grand Lyon."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Étape principale : saisie des identifiants."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]

            # Session dédiée (non partagée) avec CookieJar(unsafe=True) pour que
            # le cookie HttpOnly du login soit correctement transmis entre les 3
            # étapes du flux OAuth2 PKCE, sans interférence d'autres intégrations.
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                api = EauGrandLyonApi(session, email, password)
                try:
                    await api.authenticate()
                except AuthenticationError as err:
                    _LOGGER.warning(
                        "Erreur d'authentification Eau du Grand Lyon: %s", err
                    )
                    errors["base"] = "invalid_auth"
                except Exception as err:  # noqa: BLE001
                    _LOGGER.exception("Erreur inattendue: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    # Authentification réussie — créer l'entrée
                    await self.async_set_unique_id(email.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Eau du Grand Lyon ({email})",
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "site_url": "https://agence.eaudugrandlyon.com",
            },
        )
