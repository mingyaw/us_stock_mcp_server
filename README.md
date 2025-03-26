# US Stock Data MCP Server

A Model Context Protocol (MCP) server designed for accessing and updating US stock historical price data.

## Features

- Local Data Storage: Store stock data in CSV format locally for quick access
- Automatic Updates: Support for automatic stock data updates from Yahoo Finance
- Safe Data Writing: Use temporary files to ensure atomic and secure data writing
- Flexible Time Range: Customizable start date for data updates

## Installation

1. Ensure Python 3.x is installed
2. Clone this repository
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Start the Server

```bash
python server.py
```

The default data storage path after server startup is: `~/Library/Application Support/us-market-data/data`

You can customize the data storage path using the `US_STOCK_DATA_DIR` environment variable.

### 2. Available Features

#### MCP Tools

1. `get_local_stock_data`

   - Function: Retrieve local stock historical data
   - Parameters:
     - `symbol`: Stock symbol, e.g., 'AAPL', 'MSFT'

2. `update_stock_data`
   - Function: Update stock data
   - Parameters:
     - `symbol`: Stock symbol, e.g., 'AAPL', 'MSFT'
     - `start_date`: Start date in YYYY-MM-DD format, defaults to 2015-01-01

#### MCP Resources

- Resource URI: `usstock://{symbol}/historical`
  - Function: Provide local US stock historical price data
  - Parameters:
    - `symbol`: Stock symbol

## Data Format

The stored stock data includes the following fields:

- Date: Trading date
- Open: Opening price
- High: Highest price
- Low: Lowest price
- Close: Closing price
- Volume: Trading volume

## Dependencies

- mcp: MCP protocol implementation
- pandas: Data processing and analysis
- yfinance: Yahoo Finance data retrieval
- pydantic: Data validation and settings management

## Notes

1. Duplicate data is automatically handled during updates, keeping the latest records
2. A 5-second delay is implemented between update operations to avoid frequent API requests
3. All data operations include error handling to ensure service stability
