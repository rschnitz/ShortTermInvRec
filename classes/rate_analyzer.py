class RateAnalyzer:
    def __init__(self, hysa, tbill_1m, tbill_2m, money_market, short_term_bond):
        self.hysa = hysa
        self.tbill_1m = tbill_1m
        self.tbill_2m = tbill_2m
        self.money_market = money_market
        self.short_term_bond = short_term_bond

    def evaluate(self):
        missing_data = []
        available_data = []

        for name, option in [
            ("HYSA", self.hysa),
            ("1-Month T-Bill", self.tbill_1m),
            ("3-month T-Bill", self.tbill_2m),
            ("Money Market Fund", self.money_market),
            ("Short-Term Bond Fund", self.short_term_bond)
        ]:
            if option.rate is None:
                missing_data.append(name)
            else:
                available_data.append((name, option.rate))

        print("\n--- Missing Data ---")
        print("Could not retrieve data for:", ", ".join(missing_data))

        print("\n--- Available Data ---")
        for name, rate in available_data:
            print(f"{name}: {rate}")

        # Attempt to make a recommendation based on available data
        if self.tbill_1m.rate and self.hysa.rate:
            if self.tbill_1m.rate > self.hysa.rate:
                recommendation = "Invest in 1-Month T-Bills for higher yield and low risk."
                strength = "Strong" if not missing_data else "Moderate"
                risks = "You might miss out on liquidity if needed quickly."
                explanation = (
                    f"The 1-Month T-Bill offers a {self.tbill_1m.rate - self.hysa.rate:.2f}% higher return than HYSA. "
                    "Liquidity is medium, with low risk."
                )
            else:
                recommendation = "Hold in HYSA for flexibility and lower risk."
                strength = "Moderate"
                risks = "Missed opportunities if bond rates rise."
                explanation = "The HYSA offers a balanced choice with high liquidity and low risk."
        elif available_data:
            recommendation = "Based on limited data, consider stable options like Money Market Fund."
            strength = "Weak"
            risks = "The recommendation is based on incomplete data and may not reflect all options."
            explanation = "This recommendation is made with missing data; better to review with full data."
        else:
            recommendation = "Insufficient data to make a recommendation"
            strength = "N/A"
            risks = "N/A"
            explanation = "Please check data sources and try again."

        return recommendation, strength, risks, explanation
