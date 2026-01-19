# STDEP Backend - Usage Guide

## Project Overview

STDEP Backend is a FastAPI-based authentication and analytics server built for the SmartTrend platform. It provides secure user registration, login, and JWT-based authentication.

## Setup & Installation

### Prerequisites
- Python 3.9+
- pip

### Installation Steps

1. **Navigate to the backend directory**
   ```bash
   cd STDEP-back-end
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional)
   Create a `.env` file in the `STDEP-back-end` directory:
   ```
   SECRET_KEY=your-super-secret-key-change-this
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Available Endpoints

#### 1. **Register New User**

**Endpoint:** `POST /auth/register`

**Description:** Create a new user account with access code validation.

**Request Body:**
```json
{
  "access_code": "123456",
  "email": "user@example.com",
  "password": "securePassword123!",
  "confirm_password": "securePassword123!"
}
```

**Valid Access Codes:**
- `000000`
- `123456`
- `654321`

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid access code or passwords don't match
  ```json
  {
    "detail": "Invalid access code"
  }
  ```
- `409 Conflict` - Email already registered
  ```json
  {
    "detail": "Email already registered"
  }
  ```

#### 2. **Login**

**Endpoint:** `POST /auth/login`

**Description:** Authenticate with existing credentials and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401):**
```json
{
  "detail": "Invalid email or password"
}
```

### Authentication

Protected endpoints require the JWT token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Technology Stack

- **Framework:** FastAPI
- **Database:** SQLite (SQLAlchemy ORM)
- **Authentication:** JWT (Python-Jose)
- **Password Hashing:** Bcrypt
- **Email Validation:** Email-Validator
- **CORS:** FastAPI CORS Middleware

## Project Structure

```
STDEP-back-end/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py         # Authentication endpoints
│   │       └── analytics.py    # Analytics endpoints (placeholder)
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   └── security.py         # JWT & password utilities
│   └── db/
│       ├── models.py           # SQLAlchemy models
│       └── session.py          # Database session management
├── requirements.txt            # Python dependencies
└── README.md
```

## Database

The backend uses SQLite for data persistence. The database file (`dev.db`) is created automatically on first run.

### User Model
```
Table: users
- email (Primary Key, Unique)
- hashed_password
- full_name (Optional)
- created_at (Timestamp)
```

## Security Features

✅ **Password Hashing:** Passwords are hashed using bcrypt (never stored in plain text)
✅ **JWT Tokens:** Stateless authentication using signed JWT tokens
✅ **Access Code Validation:** Registration requires a valid access code
✅ **CORS Protection:** Configured to allow only frontend origin
✅ **Email Validation:** Email format is validated on input

## Common Use Cases

### Example 1: Register a New User (Frontend)

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    access_code: '123456',
    email: 'newuser@example.com',
    password: 'SecurePass123!',
    confirm_password: 'SecurePass123!'
  })
});

const data = await response.json();
localStorage.setItem('token', data.access_token);
```

### Example 2: Login Existing User (Frontend)

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});

const data = await response.json();
localStorage.setItem('token', data.access_token);
```

### Example 3: Make Authenticated Request

```javascript
const token = localStorage.getItem('token');
const response = await fetch('http://localhost:8000/api/v1/protected-endpoint', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

## Configuration

### Settings Location
File: `app/core/config.py`

Key configurations:
- `PROJECT_NAME` - Application name
- `API_V1_PREFIX` - API version prefix (default: `/api/v1`)
- `BACKEND_CORS_ORIGINS` - Allowed frontend origins
- `SECRET_KEY` - JWT signing key (⚠️ Change in production!)
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

### Valid Access Codes
File: `app/api/v1/auth.py` (line with `VALID_ACCESS_CODES`)

To add or modify valid codes:
```python
VALID_ACCESS_CODES = {"000000", "123456", "654321"}
```

## Troubleshooting

### Issue: "Invalid access code"
**Solution:** Ensure you're using one of the valid access codes: `000000`, `123456`, or `654321`

### Issue: "Passwords do not match"
**Solution:** Verify that `password` and `confirm_password` fields are identical

### Issue: "Email already registered"
**Solution:** Use a different email address or use the login endpoint if you already have an account

### Issue: CORS errors in frontend
**Solution:** Ensure `http://localhost:3000` is in `BACKEND_CORS_ORIGINS` in `app/core/config.py`

## Future Enhancements

- [ ] Move access codes to database
- [ ] Email verification on registration
- [ ] Password reset functionality
- [ ] Refresh token implementation
- [ ] User profile management
- [ ] Two-factor authentication
- [ ] Analytics endpoints implementation
- [ ] Rate limiting
- [ ] Logging & monitoring

## Support

For issues or questions, refer to the main project README or contact the development team.
