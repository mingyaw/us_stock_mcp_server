#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import pandas as pd
import yfinance as yf
from datetime import datetime
import tempfile
import shutil
import time
from mcp.server.fastmcp import FastMCP
from typing import Dict, Optional, List
from pydantic import BaseModel

# Set data directory
default_data_dir = Path.home() / "Library" / "Application Support" / "us-market-data" / "data"
BASE_DATA_DIR = Path(os.getenv('US_STOCK_DATA_DIR', default_data_dir))

# Ensure data directory exists
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)
print(f"Using data directory: {BASE_DATA_DIR}", file=sys.stderr)

class GetLocalStockDataArgs(BaseModel):
    symbol: str  # Stock symbol

class UpdateStockDataArgs(BaseModel):
    symbol: str
    start_date: str = "2015-01-01"  # Default start date from 2015
    
# Create MCP server
mcp = FastMCP("us-market-data")

def save_dataframe_to_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Safely save DataFrame to CSV file"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', dir=BASE_DATA_DIR) as temp_file:
            temp_path = Path(temp_file.name)
            try:
                # Save data to temporary file, excluding index
                df.to_csv(temp_path, index=False)
                # Atomically replace original file
                shutil.move(str(temp_path), str(file_path))
                print(f"Successfully saved data to {file_path}", file=sys.stderr)
            except Exception as e:
                # Ensure temporary file cleanup
                if temp_path.exists():
                    temp_path.unlink()
                raise e
    except Exception as e:
        print(f"Error saving CSV file: {str(e)}", file=sys.stderr)
        raise

def read_local_stock_data(stock_code):
    """Read CSV file for stock data"""
    try:
        file_path = BASE_DATA_DIR / f"{stock_code}.csv"
        if not file_path.exists():
            return None
        
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='Date', ascending=False)
        return df
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}", file=sys.stderr)
        return None

def update_stock_data(symbol: str, start_date: str) -> Dict[str, str]:
    """Update stock data"""
    try:
        print(f"Starting to update stock data for {symbol}...", file=sys.stderr)
        
        end_date = datetime.today().strftime("%Y-%m-%d")
        file_path = BASE_DATA_DIR / f"{symbol}.csv"
        
        # Download new data
        print(f"Downloading {symbol} data from {start_date} to {end_date}", file=sys.stderr)
        ticker = yf.Ticker(symbol)
        df_new = ticker.history(start=start_date, end=end_date)
        
        if df_new.empty:
            return {
                'status': 'error',
                'message': f'Unable to fetch data for {symbol}'
            }

        # Keep date as index, but standardize other column names
        df_new.columns = [col.capitalize() for col in df_new.columns]
        
        # Keep only required columns
        keep_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df_new = df_new[keep_columns]
        
        # Process existing data
        if file_path.exists():
            try:
                df_old = pd.read_csv(file_path)
                df_old.set_index('Date', inplace=True)
                df_old.index = pd.to_datetime(df_old.index)
                
                # Merge data and remove duplicates
                df_combined = pd.concat([df_old, df_new])
                df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
            except Exception as e:
                print(f"Error processing existing data: {str(e)}", file=sys.stderr)
                df_combined = df_new
        else:
            df_combined = df_new
        
        # Sort by date in descending order
        df_combined = df_combined.sort_index(ascending=False)
        
        # Reset index before saving
        df_combined.reset_index(inplace=True)
        
        # Save data
        try:
            save_dataframe_to_csv(df_combined, file_path)
            return {
                'status': 'success',
                'message': f'Successfully updated data for {symbol}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error saving data: {str(e)}'
            }
            
    except Exception as e:
        error_msg = f'Error updating data for {symbol}: {str(e)}'
        print(error_msg, file=sys.stderr)
        return {
            'status': 'error',
            'message': error_msg
        }

@mcp.resource("usstock://{symbol}/historical")
def get_historical_data(symbol: str):
    """Provide local US stock historical price data"""
    try:
        data = read_local_stock_data(symbol)
        if data is None:
            return {
                'status': 'error',
                'data': [],
                'message': f'Data not found for symbol {symbol}'
            }
        
        return {
            'status': 'success',
            'data': data,
            'message': f'Successfully retrieved historical data for {symbol}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'data': [],
            'message': f'Error retrieving data: {str(e)}'
        }

@mcp.tool("get_local_stock_data")
def get_local_stock_data(args: Dict) -> dict:
    """Get local stock historical data

    Args:
        symbol: Stock symbol, e.g., 'AAPL', 'MSFT'
    """
    try:
        # use UpdateStockDataArgs
        validated_args = GetLocalStockDataArgs(**args) 
        
        symbol = validated_args.symbol
        
        data = read_local_stock_data(symbol)
        if data is None:
            return {
                'status': 'error',
                'message': f'Data not found for symbol {symbol}',
                'data': []
            }
        
        return {
            'status': 'success',
            'message': f'Successfully retrieved historical data for {symbol}',
            'data': data
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error retrieving data: {str(e)}',
            'data': []
        }

@mcp.tool("update_stock_data")
def update_stock_data_tool(args: Dict) -> dict:
    """Update stock data

    Args:
        symbol: Stock symbol, e.g., 'AAPL', 'MSFT'
        start_date: Start date in YYYY-MM-DD format, defaults to 2015-01-01
    """
    try:
        # 使用 UpdateStockDataArgs 進行驗證
        validated_args = UpdateStockDataArgs(**args) 
        # 從驗證後的物件取得參數
        symbol = validated_args.symbol
        start_date = validated_args.start_date

        result = update_stock_data(symbol, start_date)
        if result['status'] == 'error':
            return result
            
        # Add delay to avoid too frequent API requests
        time.sleep(5)
        
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error updating data: {str(e)}'
        }

if __name__ == "__main__":
    try:
        print('US Stock Data MCP server is running...', file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        sys.exit(1)
