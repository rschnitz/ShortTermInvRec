# classes/investment_option.py
class InvestmentOption:
    def __init__(self, name, rate, min_deposit=0, liquidity="High"):
        self.name = name
        self.rate = rate
        self.min_deposit = min_deposit
        self.liquidity = liquidity
    
    def description(self):
        return f"{self.name}: {self.rate}% APY, Min Deposit: ${self.min_deposit}, Liquidity: {self.liquidity}, Risk: {self.risk}"
