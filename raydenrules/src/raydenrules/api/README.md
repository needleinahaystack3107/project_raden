# Rayden Rules - FastAPI Backend

REST API for climate data access and management.

## Start API

```bash
./start_api.sh
```

Access at: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

## Endpoints

### Regions
- `GET /v1/regions` - List regions
- `POST /v1/regions` - Create custom region

### Metrics
- `GET /v1/metrics?region_id={id}&from_date={date}&to_date={date}&vars={vars}`
  - Get climate metrics for region and date range
  - Variables: `lst_mean_c`, `cdd`, `hdd`, `heatwave_flag`, `uhi_index`, `anomaly_zscore`

### Alerts
- `POST /v1/alerts` - Create alert rule

### Map Tiles
- `GET /v1/tiles/{layer}/{z}/{x}/{y}.png` - Get map tile

## Example Usage

```bash
# Get regions
curl http://localhost:8000/v1/regions

# Get metrics
curl "http://localhost:8000/v1/metrics?region_id=NYC001&from_date=2025-01-01&to_date=2025-10-30&vars=lst_mean_c,anomaly_zscore"

# Create alert
curl -X POST http://localhost:8000/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{"name":"Heat Alert","region_id":"NYC001","rule":"lst_mean_c>=35","channel":"EMAIL","recipients":"admin@example.com"}'
```

## Configuration

- **API_BASE_URL**: Set in reflex_app.py (default: http://localhost:8000)
- **CORS**: Configured to allow all origins (adjust in production)
- **Mock Data**: Falls back to `data/01_raw/data_samples/metrics_mock.json`

## Development

**Run with auto-reload**:
```bash
uvicorn raydenrules.api.api:app --reload --host 0.0.0.0 --port 8000
```

**Run from project root**:
```bash
cd /path/to/raydenrules
uvicorn raydenrules.api.api:app --reload
```

## Requirements

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
