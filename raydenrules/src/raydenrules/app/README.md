# Rayden Rules - Reflex Application

Web-based dashboard for climate risk analysis and monitoring.

## Start Application

```bash
./start_app.sh
```

Access at: **http://localhost:3000**

## Structure

```
app/
├── reflex_app/
│   ├── __init__.py
│   └── reflex_app.py    # Main application
├── rxconfig.py           # Reflex configuration
├── start_app.sh          # Launcher script
└── .web/                 # Compiled frontend (generated)
```

## Pages

- **/** - Dashboard with metrics and charts
- **/alerts** - Alert configuration and monitoring
- **/regions** - Region management

## Configuration

Edit `rxconfig.py` to change:
- App name
- Database URL
- Plugins

## Development

**Run in dev mode** (auto-reload):
```bash
reflex run
```

**Build for production**:
```bash
reflex export
```

## Requirements

- Python 3.10+
- Reflex >= 0.8.0
- Running FastAPI backend on port 8000
