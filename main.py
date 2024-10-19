import argparse
from modules.data_fetch import DataFetch
from modules.data_store import DataStore
from classes.investment_option import InvestmentOption
from classes.rate_analyzer import RateAnalyzer

# Set up argument parser
parser = argparse.ArgumentParser(description="Evaluate short-term investment options.")
parser.add_argument('--force-refresh', '-f', action='store_true', help="Force fresh data, ignoring cache")
parser.add_argument('--update-position', '-u', nargs=3, metavar=('INVESTMENT', 'RATE', 'AMOUNT'),
                    help="Update the current position with investment type, rate, and amount")
parser.add_argument('--show-positions', action='store_true', help="Show the most recent investment positions")
args = parser.parse_args()

# Initialize modules
data_store = DataStore()
data_fetch = DataFetch()

# Fetch current data
if args.force_refresh:
    print("Forcing data refresh...")
    hysa_rate = data_fetch.get_hysa_rate(force_refresh=True)
    tbill_1m_rate = data_fetch.get_tbill_rate("1-month", force_refresh=True)
    tbill_2m_rate = data_fetch.get_tbill_rate("3-month", force_refresh=True)
    money_market_rate = data_fetch.get_money_market_fund_rate(force_refresh=True)
    short_term_bond_rate = data_fetch.get_short_term_bond_fund_rate(force_refresh=True)
else:
    hysa_rate = data_store.get_cached_value("hysa_rate", data_fetch.get_hysa_rate)
    tbill_1m_rate = data_store.get_cached_value("1_month_tbill_rate", lambda: data_fetch.get_tbill_rate("1-month"))
    tbill_2m_rate = data_store.get_cached_value("3_month_tbill_rate", lambda: data_fetch.get_tbill_rate("3-month"))
    money_market_rate = data_store.get_cached_value("money_market_rate", data_fetch.get_money_market_fund_rate)
    short_term_bond_rate = data_store.get_cached_value("short_term_bond_rate", data_fetch.get_short_term_bond_fund_rate)

# Create InvestmentOption instances
hysa = InvestmentOption("WealthFront HYSA", hysa_rate)
tbill_1m = InvestmentOption("1-Month T-Bill", tbill_1m_rate)
tbill_2m = InvestmentOption("3-month T-Bill", tbill_2m_rate)
money_market = InvestmentOption("BIL Money Market Fund", money_market_rate)
short_term_bond = InvestmentOption("VGSH Short-Term Bond Fund", short_term_bond_rate)

# Analyze with RateAnalyzer
rate_analyzer = RateAnalyzer(hysa, tbill_1m, tbill_2m, money_market, short_term_bond)
recommendation, strength, risks, explanation = rate_analyzer.evaluate()

# Store results
data_store.save_history(hysa_rate, tbill_1m_rate, tbill_2m_rate, money_market_rate, short_term_bond_rate, recommendation)
print("\n=== Today's Investment Recommendation ===")
print(f"Recommendation: {recommendation}")
print(f"Strength of Recommendation: {strength}")
print(f"Risks of Not Following: {risks}")
print(f"Explanation: {explanation}\n")

# Add a check if there were any issues with missing data
if "Missing data" in explanation:
    print("\n--- Missing Data Warning ---")
    print("Some data sources were unavailable, which may affect the accuracy of this recommendation.")
    print("Please try again later or check the status of the data sources.\n")
