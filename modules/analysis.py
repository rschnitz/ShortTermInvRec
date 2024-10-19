class Analysis:
    def make_recommendation(self, hysa_rate, one_month_rate, two_month_rate, fed_sentiment):
        if one_month_rate > hysa_rate or two_month_rate > hysa_rate:
            if fed_sentiment in ["HOLD", "RAISE"]:
                return "Invest in 1- or 3-month T-Bills"
            else:
                return "Hold in HYSA"
        else:
            if fed_sentiment == "LOWER":
                return "Consider dividend-paying funds or short-term bonds"
            return "Re-evaluate next week"
