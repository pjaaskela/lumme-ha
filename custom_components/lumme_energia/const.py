DOMAIN = "lumme_energia"

AUTH_URL = (
    "https://kirjaudu.lumme-energia.fi/auth/realms/Lumme/protocol/openid-connect/auth"
    "?client_id=exove-oma-lumme"
    "&redirect_uri=https://oma.lumme-energia.fi/"
    "&response_type=code&scope=openid&state=lumme_ha"
)
API_BASE = "https://api-omalumme-prod.azure-api.net/FA-OmaLumme-Prod"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

UPDATE_INTERVAL_MINUTES = 15
TOKEN_REFRESH_HOURS = 1

SENSOR_DAILY = "daily_consumption"
SENSOR_MONTHLY = "monthly_consumption"
SENSOR_HOURLY = "last_hour_consumption"
