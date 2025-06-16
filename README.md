# Stock Prices Flask API

A simple Flask REST API for managing stock price data using SQLite database.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The server will start at `http://localhost:5000`

## API Endpoints

### Create a new stock price record
- **POST** `/api/stocks`
- Request body example:
```json
{
    "date": "2024-03-20",
    "stock": "AAPL",
    "open": 150.25,
    "high": 152.50,
    "low": 149.75,
    "close": 151.80,
    "volume": 1000000,
    "change_pct": 1.25
}
```

### Get all stock prices
- **GET** `/api/stocks`

### Get a specific stock price
- **GET** `/api/stocks/<stock_id>`

### Update a stock price
- **PUT** `/api/stocks/<stock_id>`
- Request body example (include only fields to update):
```json
{
    "close": 152.00,
    "volume": 1200000
}
```

### Delete a stock price
- **DELETE** `/api/stocks/<stock_id>`

## Database

The application uses SQLite as the database. The database file (`stocks.db`) will be created automatically when you first run the application. 