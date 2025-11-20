# STDEP Backend

Backend API for the Smart Trend Driven E-commerce Pilot (STDEP) application.

Built with **FastAPI** and **SQLAlchemy**, this service handles:
- User authentication & authorization
- Analytics and forecasting
- Database operations

## Quick Start

### Prerequisites

- **Python 3.9+** (check with `python --version`)
- **pip** (included with Python)

### Setup

1. **Clone and navigate to the backend folder:**
   ```powershell
   cd STDEP-back-end
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   # Create virtual environment
   python -m venv .venv
   
   # Activate it (Windows PowerShell)
   .venv\Scripts\Activate.ps1
   
   # Activate it (Windows CMD)
   .venv\Scripts\activate.bat
   
   # Activate it (Mac/Linux)
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```powershell
   # Copy the example file
   Copy-Item .env.example -Destination .env
   
   # Edit .env with your configuration (optional for local dev)
   # On Windows, you can use: notepad .env
   ```

### Running the Server

Start the development server with auto-reload:

```powershell
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Project Structure

```
STDEP-back-end/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py         # Authentication endpoints
│   │       └── analytics.py    # Analytics endpoints
│   ├── core/
│   │   ├── config.py           # Configuration & settings
│   │   └── security.py         # Security & token utilities
│   └── db/
│       └── session.py          # Database session management
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
└── README.md
```

### API Endpoints

#### Authentication
- `POST /api/v1/auth/login` — Login with email & password
- `POST /api/v1/auth/signup` — Create a new user account

#### Analytics
- `GET /api/v1/analytics/forecast` — Get sales forecast data
- `GET /api/v1/analytics/history` — Get historical analytics

### Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

### Troubleshooting

**"ModuleNotFoundError: No module named 'fastapi'"**
- Make sure your virtual environment is activated and dependencies are installed:
  ```powershell
  pip install -r requirements.txt
  ```

**"Address already in use" (port 8000 in use)**
- Use a different port:
  ```powershell
  uvicorn app.main:app --reload --port 8001
  ```

**Virtual environment not activating**
- If PowerShell execution policy blocks the script, run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Development Tips

- **Auto-reload** is enabled by default with `--reload` flag; changes will reflect immediately.
- **Interactive API docs** available at `/docs` to test endpoints live.
- Database connections and secrets go in `.env` (never commit this file).

### Team Notes

- Everyone should create their own `.env` file from `.env.example`.
- Do **not** commit `.env` files (only `.env.example` is tracked).
- Ensure the backend is running before starting the frontend (frontend makes API calls to `http://localhost:8000`).

