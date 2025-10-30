# Rayden Rules - Quick Start Guide

## 🚀 Start the Application

### 1. Start Backend API
```bash
cd src/raydenrules/api
./start_api.sh
```
**Access**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### 2. Start Frontend App
```bash
cd src/raydenrules/app
./start_app.sh
```
**Access**: http://localhost:3000

## 📄 Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | http://localhost:3000/ | Metrics, charts, KPIs |
| Alerts | http://localhost:3000/alerts | Alert configuration |
| Regions | http://localhost:3000/regions | Region management |

## 🎯 Features

**Dashboard**
- Select region (NYC, LA, Chicago, Miami)
- Choose date range
- View KPIs (Temperature, Heatwaves, Energy, Anomaly)
- Interactive charts (Line/Bar/Area)

**Alerts**
- View configured alerts
- Create new alerts with thresholds
- Set notification channels (Email/Slack/Webhook)
- Configure severity (LOW/MEDIUM/HIGH/CRITICAL)

**Regions**
- View built-in regions
- Upload custom GeoJSON regions
- Manage geographic areas

## 🛠️ Development

**Install**
```bash
pip install -r requirements.txt
```

**Test**
```bash
pytest
```

**Code Quality**
```bash
ruff check .
black .
```

## 📦 Structure

```
raydenrules/
├── src/raydenrules/
│   ├── api/           # FastAPI backend
│   ├── app/           # Reflex frontend
│   │   └── reflex_app/
│   └── pipelines/     # Kedro pipelines
├── data/              # Data layers
└── conf/              # Configuration
```

## 🔧 Troubleshooting

**Port in use**
```bash
# Kill process on port
lsof -ti:3000 | xargs kill -9
```

**Module not found**
```bash
pip install -r requirements.txt
```

**Data not loading**
- Check `data/01_raw/data_samples/metrics_mock.json` exists
- Ensure API is running on port 8000
```
data/01_raw/data_samples/metrics_mock.json
```

### API Not Connecting
Make sure FastAPI is running on port 8000, or the app will use mock data.

## 📚 Documentation

- **Migration Guide**: `src/raydenrules/app/MIGRATION_GUIDE.md`
- **Reflex README**: `src/raydenrules/app/REFLEX_README.md`
- **Main README**: `README.md`

## 💡 Tips

1. **Hot Reload**: Changes to `reflex_app.py` auto-reload
2. **State Debugging**: Check terminal for state changes
3. **API Fallback**: App works without API using mock data
4. **Clean Start**: Delete `reflex.db` to reset state

## 🆘 Need Help?

- Reflex Docs: https://reflex.dev/docs/
- Project Issues: Check terminal output for errors
- Rollback: See MIGRATION_GUIDE.md for reverting to Streamlit
