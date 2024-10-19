import pandas as pd
from datetime import datetime
import numpy as np

class DataStore:
    def __init__(self, history_file='investment_history.csv', positions_file='current_positions.csv'):
        self.history_file = history_file
        self.positions_file = positions_file
        self.history_df = self.load_history()
        self.positions_df = self.load_positions()

    def load_history(self):
        try:
            return pd.read_csv(self.history_file)
        except FileNotFoundError:
            return pd.DataFrame(columns=["Date", "HYSA Rate", "1-Month T-Bill", "3-month T-Bill", "Bond Rate", "Stock Price", "Recommendation"])

    def load_positions(self):
        try:
            return pd.read_csv(self.positions_file)
        except FileNotFoundError:
            return pd.DataFrame(columns=["Date", "Investment", "Rate", "Amount", "Details"])


    def save_history(self, hysa_rate, tbill_1m_rate, tbill_2m_rate, money_market_rate, short_term_bond_rate, recommendation):
        today = datetime.now().strftime("%Y-%m-%d")
        new_data = pd.DataFrame([{
            "Date": today,
            "HYSA Rate": hysa_rate,
            "1-Month T-Bill": tbill_1m_rate,
            "3-month T-Bill": tbill_2m_rate,
            "Money Market Rate": money_market_rate,
            "Short-Term Bond Rate": short_term_bond_rate,
            "Recommendation": recommendation
        }])

        # Convert None to NaN for consistency
        new_data = new_data.replace({None: np.nan})

        # Address future behavior change in downcasting explicitly
        new_data = new_data.infer_objects()

        # Drop rows where all rate columns are NaN
        rate_columns = ["HYSA Rate", "1-Month T-Bill", "3-month T-Bill", "Money Market Rate", "Short-Term Bond Rate"]
        new_data = new_data.dropna(subset=rate_columns, how='all')

        # Only concatenate if new_data is non-empty
        if not new_data.empty:
            print("new_data is not empty, proceeding with concatenation.")
            self.history_df = pd.concat([self.history_df, new_data], ignore_index=True)
            self.history_df.to_csv(self.history_file, index=False)
        else:
            print("No valid data to save to history. new_data is empty after filtering.")

    def get_cached_value(self, key, fetch_func):
        # Use cache and refetch if expired
        data = fetch_func()
        return data
