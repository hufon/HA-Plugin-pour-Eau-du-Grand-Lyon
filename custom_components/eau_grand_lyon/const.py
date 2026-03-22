"""Constantes pour l'intégration Eau du Grand Lyon."""

DOMAIN = "eau_grand_lyon"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Intervalle de mise à jour : 1x par jour (données mensuelles, évite les blocages WAF)
UPDATE_INTERVAL_HOURS = 24
