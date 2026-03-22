"""Constantes pour l'intégration Eau du Grand Lyon."""

DOMAIN = "eau_grand_lyon"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Options configurables
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
DEFAULT_UPDATE_INTERVAL_HOURS = 24

CONF_TARIF_M3 = "tarif_m3"
# Tarif indicatif Eau du Grand Lyon 2024 — TTC, tout inclus (eau + assainissement + taxes)
# Source : https://agence.eaudugrandlyon.com — à vérifier sur votre facture
DEFAULT_TARIF_M3 = 5.20

# Intervalle de mise à jour par défaut (données mensuelles, évite les blocages WAF)
UPDATE_INTERVAL_HOURS = DEFAULT_UPDATE_INTERVAL_HOURS
