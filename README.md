# Lumme Energia — Home Assistant integration

Custom HACS integration for [Lumme Energia](https://www.lumme-energia.fi/) electricity customers in Finland.

Fetches your daily and monthly electricity consumption from the OmaLumme customer portal.

## Features

- **Daily consumption** (kWh) — previous day's usage (data is ~1 day delayed)
- **Monthly consumption** (kWh) — running total for the current month
- Automatic token refresh
- Works with HA Energy dashboard

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/pjaaskel/lumme-ha` as type **Integration**
3. Find "Lumme Energia" and install it
4. Restart Home Assistant

### Manual

Copy `custom_components/lumme_energia/` into your HA `config/custom_components/` folder and restart.

## Configuration

1. Go to **Settings → Integrations → + Add integration**
2. Search for **Lumme Energia**
3. Enter your OmaLumme username (email) and password

## Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.paivan_kulutus` | Previous day's consumption | kWh |
| `sensor.kuukauden_kulutus` | Current month's consumption | kWh |

## Notes

- Requires an active OmaLumme account at [oma.lumme-energia.fi](https://oma.lumme-energia.fi/)
- Data is fetched every 15 minutes (API data itself is delayed ~24 h)
- Only tested with a single metering point

## Support

If this saves you time, consider [buying me a coffee ☕](https://ko-fi.com/pjaaskel)

## License

MIT
