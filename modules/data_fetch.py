import json
import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import yfinance as yf


nasdaq_key = "a9DQaUgyyyRzrAM298Wu"
fred_key = "42e681bda2bf55ca9a444eb231842b62"
quandl_key = "a9DQaUgyyyRzrAM298Wu"
alphaVantage_key = "9T0OSKE5KGFN4XNL"

class DataFetch:
    cache_file = 'cache.json'
    
    def __init__(self):
        # Define expiration rules with relevant market hours
        self.staleness_rules = {
            'tbill_rate': {'duration': timedelta(days=1), 'market_hours': (16, 0)},  # 4 p.m. EST
            'hysa_rate': {'duration': timedelta(weeks=1), 'market_hours': None},     # Weekly update
            'mm_rate': {'duration': timedelta(days=1)},  # Add this if missing
            'bond_rate': {'duration': timedelta(days=1), 'market_hours': (9, 0)},    # 9 a.m. EST
            'bond_data': {'duration': timedelta(days=1), 'market_hours': (9, 0)},    # 9 a.m. EST
            'quandl_data': {'duration': timedelta(days=1), 'market_hours': (9, 0)},  # 9 a.m. EST
        }

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}


    def save_cache(self, cache):
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)
        print(f"Cache saved successfully with the following data:")
        for key, value in cache.items():
            print(f"  {key}: {value}")


    def is_stale(self, expiration_time, data_type):
        # If no expiration time is set, treat as stale
        if not expiration_time:
            return True

        expiration_duration = self.staleness_rules.get(data_type, {}).get('duration', timedelta(days=1))
        market_hours = self.staleness_rules.get(data_type, {}).get('market_hours')

        cache_expired = datetime.now() > datetime.fromisoformat(expiration_time)
        
        # Check if market is open based on hours, skip weekends for market-specific data
        if market_hours:
            now = datetime.now()
            is_market_open = now.weekday() < 5 and (now.hour, now.minute) >= market_hours
            return cache_expired and is_market_open
        else:
            return cache_expired

    def fetch_with_expiry(self, key, fetch_func, data_type, force_refresh=False):
        cache = self.load_cache()
        cache_entry = cache.get(key, {})

        # Treat legacy format as stale
        if isinstance(cache_entry, float):
            print(f"\nLegacy format detected for {key}. Treating as stale data.")
            cache_entry = {}

        expiration_time = cache_entry.get('expires_at')

        # Skip cache if forced refresh is enabled
        if force_refresh or self.is_stale(expiration_time, data_type):
            print(f"\nFetching fresh data for: {key}")
            result = fetch_func()
            if result is not None:
                expires_at = (datetime.now() + self.staleness_rules[data_type]['duration']).isoformat()
                cache[key] = {'value': result, 'expires_at': expires_at}
                self.save_cache(cache)
                print(f"  Updated cache for {key}:")
                print(f"    Value: {result}")
                print(f"    Expires at: {expires_at}\n")
            else:
                print(f"  Failed to fetch data for {key}.\n")
            return result

        print(f"Using cached data for {key}:")
        print(f"  Value: {cache_entry.get('value')}")
        print(f"  Expires at: {expiration_time}\n")
        return cache_entry.get('value')

    def fetch_tbill_rate_from_fred(self, series_id):
        api_key = fred_key
        print(f"Attempting to fetch T-Bill rate from FRED for series ID: {series_id}")
        api_url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json"
        print(f"API URL: {api_url}")
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            # Adjust based on response format
            observations = data.get('observations')
            if not observations:
                print(f"No observations found in FRED data for {series_id}")
                return None

            latest_observation = observations[-1]
            rate = float(latest_observation.get('value'))
            print(f"Fetched {series_id} T-Bill rate: {rate}")
            return rate

        except requests.exceptions.RequestException as e:
            print(f"Network or request error when fetching T-Bill rate: {e}")
        except ValueError as e:
            print(f"Error parsing T-Bill rate response as JSON: {e}")
        except KeyError as e:
            print(f"Unexpected data format when fetching T-Bill rate, missing key: {e}")
        return None



    def fetch_hysa_rate_from_web(self):
        print("Attempting to fetch the HYSA rate from the web source.")
        try:
            # Assuming the use of requests to get the rate
            rate = self.fetch_hysa_rate_from_bankrate()

            if rate is None:
                print("HYSA rate key not found in the response.")
            else:
                print(f"Fetched HYSA rate successfully: {rate}")
            return rate

        except requests.exceptions.RequestException as e:
            print(f"Network or request error when fetching HYSA rate: {e}")
        except ValueError as e:
            print(f"Error parsing HYSA rate response as JSON: {e}")
        except KeyError as e:
            print(f"Unexpected data format when fetching HYSA rate, missing key: {e}")
        return None
    
    def fetch_hysa_rate_from_bankrate(self):
        url = "https://www.bankrate.com/banking/savings/high-yield-savings-rates/"
        url = "https://www.bankrate.com/banking/savings/best-high-yield-interests-savings-accounts/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the first listed HYSA rate (update selector as per website structure)
        rate_tag = soup.find("div", class_="wrt-WowLowRates-metricValue")
        if rate_tag:
            rate = rate_tag.text.split('%')[0]
            return float(rate)
        
        return None


    def get_bond_data(self, symbol):
        return self.fetch_with_expiry(
            f"bond_data_{symbol}",
            lambda: self.fetch_bond_data_from_alpha(symbol),
            'bond_data'
        )

    def fetch_bond_data_from_alpha(self, symbol):
        api_key = alphaVantage_key
        api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        
        response = requests.get(api_url)
        data = response.json()
        try:
            latest_date = list(data["Time Series (Daily)"].keys())[0]
            closing_price = data["Time Series (Daily)"][latest_date]["4. close"]
            return float(closing_price)
        except KeyError:
            return None

    def get_quandl_data(self, dataset_code):
        return self.fetch_with_expiry(
            f"quandl_data_{dataset_code}",
            lambda: self.fetch_quandl_data_from_api(dataset_code),
            'quandl_data'
        )

    def fetch_quandl_data_from_api(self, dataset_code):
        api_key = quandl_key
        api_url = f"https://www.quandl.com/api/v3/datasets/{dataset_code}.json?api_key={api_key}"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Check for HTTP errors
            if response.text.strip():  # Ensure response is not empty
                data = response.json()
                latest_value = data["dataset"]["data"][0][1]
                return float(latest_value)
            else:
                print("Empty response from Quandl API.")
                return None
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        except ValueError as json_err:
            print(f"JSON decode error: {json_err}")
        except KeyError:
            print("Unexpected data format from Quandl API.")
        return None  # Return None if an error occurs

    def get_fund_data(self, symbol):
        return self.fetch_with_expiry(
            f"fund_data_{symbol}",
            lambda: self.fetch_fund_data_from_alpha(symbol),
            'fund_data'
        )

    def fetch_fund_data_from_alpha(self, symbol):
        api_key = alphaVantage_key
        api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            latest_date = list(data["Time Series (Daily)"].keys())[0]
            closing_price = data["Time Series (Daily)"][latest_date]["4. close"]
            return float(closing_price)
        except requests.exceptions.RequestException as e:
            print(f"Request error for Alpha Vantage: {e}")
        except KeyError:
            print("Unexpected data format from Alpha Vantage.")
        return None


    def fetch_etf_rate(self, symbol):
        print(f"\nAttempting to fetch data for ETF: {symbol}")
        
        # Try Alpha Vantage first
        rate = self.fetch_etf_rate_alpha(symbol)
        if rate is None:
            print(f"  Alpha Vantage failed for {symbol}. Falling back to yfinance.")
            rate = self.fetch_etf_rate_yf(symbol)
        
        if rate is None:
            print(f"  Both data sources failed for {symbol}.")
        else:
            print(f"  Successfully fetched rate for {symbol}: {rate}")
        
        return rate


    def fetch_etf_rate_alpha(self, symbol):
        api_key = alphaVantage_key
        api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            if 'Time Series (Daily)' not in data:
                print(f"Alpha Vantage response missing data for {symbol}: {data}")
                return None
            latest_date = list(data["Time Series (Daily)"].keys())[0]
            closing_price = data["Time Series (Daily)"][latest_date]["4. close"]
            return float(closing_price)
        except Exception as e:
            print(f"Error fetching data from Alpha Vantage for {symbol}: {e}")
            return None

    def fetch_etf_rate_yf(self, symbol):
        try:
            etf = yf.Ticker(symbol)
            data = etf.history(period="1d")
            if data.empty:
                print(f"yfinance returned empty data for {symbol}.")
                return None
            closing_price = data["Close"].iloc[-1]
            return closing_price
        except Exception as e:
            print(f"Error fetching data from yfinance for {symbol}: {e}")
            return None

    def get_hysa_rate(self, force_refresh=False):
        print("\n--- Fetching HYSA Rate ---")
        return self.fetch_with_expiry(
            "hysa_rate",
            self.fetch_hysa_rate_from_web,
            'hysa_rate',
            force_refresh=force_refresh
        )

    def get_tbill_rate(self, duration, force_refresh=False):
        print(f"\n--- Fetching T-Bill Rate ---")
        print(f"Requested duration: {duration}")

        if duration == "1-month":
            print("Attempting to fetch 1-month T-Bill rate.")
            rate = self.fetch_with_expiry(
                "1_month_tbill_rate",
                lambda: self.fetch_tbill_rate_from_fred("DGS1MO"),
                'tbill_rate',
                force_refresh=force_refresh
            )
        elif duration == "3-month":
            print("Attempting to fetch 3-month T-Bill rate.")
            rate = self.fetch_with_expiry(
                "3_month_tbill_rate",
                lambda: self.fetch_tbill_rate_from_fred("DGS3MO"),
                'tbill_rate',
                force_refresh=force_refresh
            )
        else:
            print("Invalid duration specified for T-Bill rate.")
            return None

        if rate is None:
            print(f"Failed to fetch {duration} T-Bill rate.")
        else:
            print(f"Fetched {duration} T-Bill rate: {rate}")
        
        return rate


    def get_money_market_fund_rate(self, force_refresh=False):
        print("\n--- Fetching Money Market Fund Rate ---")
        return self.fetch_with_expiry(
            "money_market_rate",
            lambda: self.fetch_etf_rate("BIL"),
            'mm_rate',
            force_refresh=force_refresh
        )

    def get_short_term_bond_fund_rate(self, force_refresh=False):
        print("\n--- Fetching Short-Term Bond Fund Rate ---")
        return self.fetch_with_expiry(
            "short_term_bond_rate",
            lambda: self.fetch_etf_rate("VGSH"),
            'bond_rate',
            force_refresh=force_refresh
        )
