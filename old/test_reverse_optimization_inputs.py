historical_return_data = pd.DataFrame({
    "Cash": [0.06, 0.07, 0.06, 0.05],
    "Bond": [0.02, -0.02, 0.07, 0.11],
    "Stock": [-0.28, -0.02, 0.12, 0.16]
})
historical_risk_free_returns = historical_return_data['Cash']
market_portfolio_weights = pd.Series({
    "Cash": 0.1,
    "Bond": 0.6,
    "Stock": 0.3
})
market_risk_premium = 0.04
current_risk_free_rate = 0.05
