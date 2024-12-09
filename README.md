# Inventory Management System

Cross-border liquidity services.

## Setup

Install dependencies:
   ```bash
   poetry install
   ```

Start the database:
   ```bash
   docker compose up -d
   ```

Set up the database:
   ```bash
   alembic upgrade head
   ```

Start the application:
   ```bash
   bash ./start.sh
   ```

## API Endpoints

- `POST /transfer` - Create a new currency transfer
- `GET /transfer/{id}` - Get transfer status
- `POST /fx-rate` - Update currency exchange rate
- `GET /fx-rate/{base}-{quote}` - Get latest exchange rate

### Examples

### Create a new currency transfer
```bash
curl -X POST http://localhost:8000/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "target_currency": "EUR",
    "source_amount": "1000.00"
  }'
```

### Get transfer status
```bash
curl http://localhost:8000/transfer/123
```

### Update currency exchange rate
```bash
curl -X POST http://localhost:8000/fx-rate \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "USD/EUR",
    "rate": "0.92",
    "timestamp": "2024-03-19T10:00:00Z"
  }'
```

### Get latest exchange rate
```bash
curl http://localhost:8000/fx-rate/USD-EUR
```
