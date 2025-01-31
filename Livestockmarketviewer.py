import requests
from bs4 import BeautifulSoup
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import time
import random

# Setting up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stock:
    def __init__(self, id, name, time, data):
        self.id = id
        self.name = name
        self.time = time
        self.data = data

    def __repr__(self):
        return f"Stock(ID={self.id}, name={self.name}, time={self.time}, data={self.data})"

def log_cpu_utilization():
    """Log the current CPU utilization."""
    cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage over 1 second
    logger.info(f"Current CPU utilization: {cpu_usage}%")

def get_stock_names_and_ids(seq):

    url = f"https://thirdeyestocksmaneger.onrender.com/api/stocksbatch/126/stocksbatch/{seq}"
    try:
        logger.info(f"Fetching stock names and IDs from the API for seq {seq}...")
        response = requests.get(url)
        response.raise_for_status()  # Will raise HTTPError for bad responses
        logger.info("Successfully fetched stock names and IDs.")
        return response.json()  # Returns dictionary with stock IDs and names
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching stock names and IDs: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching stock names and IDs: {e}")
        return {}

def map_ticker_name(ticker_name):
    """Map stock names to Yahoo Finance accepted format."""
    try:
        if ticker_name.endswith(" NSE"):
            mapped_name = ticker_name.replace(" ", ":")
            logger.debug(f"Mapped stock name {ticker_name} to {mapped_name} for Yahoo Finance.")
            return mapped_name
        else:
            logger.warning(f"Ticker name {ticker_name} did not need mapping.")
            return ticker_name
    except Exception as e:
        logger.error(f"Error mapping ticker name {ticker_name}: {e}")
        return ticker_name

def get_stock_data(ticker_name, stock_id):
    try:
        logger.info(f"Fetching data for stock: {ticker_name} (ID: {stock_id})")
        
        # Map the ticker name to Yahoo Finance format
        yahoo_ticker_name = map_ticker_name(ticker_name)

        url = f"https://www.google.com/finance/quote/{yahoo_ticker_name}"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad responses
        logger.info(f"Successfully fetched data for {ticker_name} (ID: {stock_id}) from Yahoo Finance.")

        # Log CPU utilization during the request process
        # log_cpu_utilization()

        # Parse the response with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        elements_1 = soup.find_all(class_="YMlKec fxKbKc")
        elements_2 = soup.find_all(class_="Ez2Ioe")
        timestamp_element = soup.find("div", class_="ygUjEc")  # Extract timestamp & exchange details

        stock_map = {
            "Current Price": elements_1[0].get_text(strip=True) if len(elements_1) > 0 else None,
            "Today's change": elements_2[0].get_text(strip=True) if len(elements_2) > 0 else None,
            "Timestamp & Exchange": timestamp_element.get_text(strip=True) if timestamp_element else None,
        }

        # Extract other stock information dynamically
        for section in soup.find_all("div", class_="gyFHrc"):
            key_element = section.find("div", class_="mfs7Fc")  # Extracts the label
            value_element = section.find("div", class_="P6K39c")  # Extracts the value

            if key_element and value_element:
                key = key_element.text.strip()
                value = value_element.text.strip()
                stock_map[key] = value 



        # # Extract whether the market is open or not
        last_updated_time = ""
        # Create a Stock object with the data
        stock = Stock(id=stock_id, name=ticker_name, time=last_updated_time, data=stock_map)
        return stock

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for {ticker_name} (ID: {stock_id}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching data for {ticker_name} (ID: {stock_id}): {e}")
        return None

def get_multiple_stock_data():
    try:
        logger.info("Fetching stock data for multiple stocks...")
        stock_objects = []
        stock_names_and_ids = get_stock_names_and_ids(1)
        stock_names_and_ids1 = get_stock_names_and_ids(2)
        stock_names_and_ids.update(stock_names_and_ids1)

        if not stock_names_and_ids:
            logger.error("No stock names and IDs were fetched. Aborting process.")
            return []

        # Using ThreadPoolExecutor to fetch data concurrently for stocks
        with ThreadPoolExecutor(max_workers=40) as executor:
            futures = {
                executor.submit(get_stock_data, ticker_name, stock_id): (ticker_name, stock_id)
                for stock_id, ticker_name in stock_names_and_ids.items()
            }
            
            # Wait for all futures to complete and process results
            for future in as_completed(futures):
                ticker_name, stock_id = futures[future]
                try:
                    stock_data = future.result()
                    if stock_data:
                        stock_objects.append(stock_data)
                except Exception as e:
                    logger.error(f"Error while processing stock data for {ticker_name} (ID: {stock_id}): {e}")

        logger.info("Successfully fetched stock data for multiple stocks.")
        return stock_objects
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching data for multiple stocks: {e}")
        return []

def main():
    try:
        # Fetch stock names and IDs once
        stock_names_and_ids = get_stock_names_and_ids(1)
        stock_names_and_ids1 = get_stock_names_and_ids(2)
        stock_names_and_ids.update(stock_names_and_ids1)

        
        while True:
            # Fetch stock data every 30 seconds
            stocks_data = get_multiple_stock_data()
            if stocks_data:
                num=1
                    
            else:
                logger.warning("No stock data found.")

            # Sleep for 30 seconds before fetching again
            stocks_data = []
            
    except Exception as e:
        logger.error(f"Error occurred in main function: {e}")

if __name__ == "__main__":
    # Monitor CPU utilization while running the program
    # log_cpu_utilization()  # Initial log
    main()
    # log_cpu_utilization()  # Final log after completion
