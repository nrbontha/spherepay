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
