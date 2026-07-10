"""Generate data/ticker_info.json from the ticker mapping."""
import json

mapping = [
    ("U.S. Large Cap Equities", "MSCI USA (USD) Total Return Index", "NDDUUS", "MSCI"),
    ("U.S. Value", "MSCI USA Value (USD) Total Return Index", "M1USVA", "MSCI"),
    ("U.S. Growth", "MSCI USA Growth (USD) Total Return Index", "M1USGR", "MSCI"),
    ("U.S. Momentum", "MSCI USA Momentum (USD) Total Return Index", "M1USMO", "MSCI"),
    ("U.S. Quality", "MSCI USA Quality (USD) Total Return Index", "M1USQU", "MSCI"),
    ("U.S. Low Volatility", "MSCI USA Minimum Volatility (USD) Total Return Index", "M1USMVOL", "MSCI"),
    ("U.S. Small Cap Equities", "Russell 2000 Total Return Index", "RU20INTR", "FTSE Russell"),
    ("U.S. Small Cap Value", "Russell 2000 Value Total Return Index", "RU20VATR", "FTSE Russell"),
    ("International Equities", "MSCI EAFE Net Return Index USD", "NDDUEAFE", "MSCI"),
    ("International Value", "MSCI EAFE Value Net Return Index USD", "NDDUEAFV", "MSCI"),
    ("Global Equities", "MSCI ACWI Net Return Index USD", "NDUEACWF", "MSCI"),
    ("Emerging Market Equities", "MSCI Emerging Markets Net Return Index USD", "NDUEEGF", "MSCI"),
    ("Emerging Markets Value", "MSCI Emerging Markets Value Net Return Index USD", "NDUEVEMF", "MSCI"),
    ("U.S. Treasury Ladder", "ReSolve U.S. Treasury Ladder Index", "N/A", "ReSolve Asset Management"),
    ("U.S. Core Fixed Income", "Bloomberg US Agg Total Return Value Unhedged USD", "LBUSTRUU", "Bloomberg"),
    ("U.S. Treasuries", "Bloomberg US Treasury Total Return Index", "LUATTRUU", "Bloomberg"),
    ("Short-Term U.S. Treasuries", "Bloomberg US Treasury 1-5 Year Total Return Index", "LTR1TRUU", "Bloomberg"),
    ("Intermediate-Term U.S. Treasuries", "Bloomberg US Intermediate Treasury TR Index Value Unhedged USD", "LT08TRUU", "Bloomberg"),
    ("Long-Term U.S. Treasuries", "Bloomberg US Long Treasury Total Return Index Value Unhedged USD", "LUTLTRUU", "Bloomberg"),
    ("U.S. Corporate Fixed Income", "Bloomberg US Corporate Total Return Value Unhedged USD", "LUACTRUU", "Bloomberg"),
    ("Short-Term Investment Grade Fixed Income", "Bloomberg US Credit 1-5 Years Total Return Index Value Unhedged USD", "LDC5TRUU", "Bloomberg"),
    ("Intermediate-Term Investment Grade Fixed Income", "Bloomberg US Credit Corp 5-10Y Total Return Index Value Unhedged USD", "BCR5TRUU", "Bloomberg"),
    ("Long-Term Investment Grade Fixed Income", "Bloomberg U.S. 10+ Year Corporate Bond Total Return Index Unhedged USD", "I13284US", "Bloomberg"),
    ("High Yield Fixed Income", "Bloomberg US Corporate High Yield Total Return Index Value Unhedged USD", "LF98TRUU", "Bloomberg"),
    ("Mortgage Backed Securities", "Bloomberg US MBS Index Total Return Value Unhedged USD", "LUMSTRUU", "Bloomberg"),
    ("International Treasuries", "Bloomberg Global Treasury ex-US Capped Total Return Index Value Unhedged USD", "LGT1TRUU", "Bloomberg"),
    ("Global Core Fixed Income", "Bloomberg Global-Aggregate Total Return Index Value Unhedged USD", "LEGATRUU", "Bloomberg"),
    ("Emerging Market Bonds (Local)", "JPMorgan GBI-EM Global Diversified (Local Currency)", "JGENVUUG", "J.P. Morgan"),
    ("Emerging Market Bonds (USD)", "JPMorgan EMBI Global Diversified (USD)", "JPGCCOMP", "J.P. Morgan"),
    ("Real Estate", "Dow Jones U.S. Select REIT Total Return Index", "DWRTFT", "S&P Dow Jones Indices"),
    ("Commodities", "S&P GSCI Index (Spot)", "SPGSCI", "S&P Dow Jones Indices"),
    ("Gold", "XAU Currency (Gold Spot USD)", "XAU Curncy", "Bloomberg"),
    ("Digital Assets", "S&P Bitcoin Index", "SPBTC", "S&P Dow Jones Indices"),
    ("Short-Term TIPS", "Bloomberg US Treasury TIPS 0-5 Years Total Return Index Unhedged USD", "LTP5TRUU", "Bloomberg"),
    ("Intermediate-Term TIPS", "Bloomberg US Treasury Inflation Notes TR Index Value Unhedged USD", "LBUTTRUU", "Bloomberg"),
    ("Long Volatility", "CBOE Eurekahedge Long Volatility Hedge Fund Index", "EHFI451", "EurekaHedge"),
    ("Tail Risk Hedges", "CBOE Eurekahedge Tail Risk Hedge Fund Index", "EHFI453", "EurekaHedge"),
    ("Equity Long/Short", "PivotalPath Equity Diversified: Global Long/Short Index", "EQDGLS", "PivotalPath"),
    ("Hedge Funds", "PivotalPath Composite EW Index", "HFCEW", "PivotalPath"),
    ("Equity Market Neutral", "EurekaHedge Equity Market Neutral Hedge Fund Index", "EHFI751", "EurekaHedge"),
    ("Event Driven", "PivotalPath Event Driven Index", "EVD", "PivotalPath"),
    ("Merger Arbitrage", "PivotalPath Event Driven: Merger Arbitrage Index", "EVDMER", "PivotalPath"),
    ("Relative Value", "PivotalPath Credit: Relative Value Index", "CRDREL", "PivotalPath"),
    ("Managed Futures CTA", "PivotalPath Managed Futures Index", "MFT", "PivotalPath"),
    ("Managed Futures Trend", "SG Trend Index", "NEIXCTAT", "Societe Generale"),
    ("Risk Parity (10%)", "S&P Risk Parity Index - 10% Target Volatility", "SPRP10UT", "S&P Dow Jones Indices"),
    ("Risk Parity (12%)", "S&P Risk Parity Index - 12% Target Volatility", "SPRP12UT", "S&P Dow Jones Indices"),
    ("Risk Parity (15%)", "S&P Risk Parity Index - 15% Target Volatility", "SPRP15UT", "S&P Dow Jones Indices"),
    ("Global Macro", "PivotalPath Global Macro Index", "GBM", "PivotalPath"),
    ("Global Macro (Commodities)", "PivotalPath Global Macro: Commodities Index", "GBMCOM", "PivotalPath"),
    ("Systematic Global Macro", "PivotalPath Global Macro: Quantitative Index", "GBMQNT", "PivotalPath"),
    ("Global Macro (Risk Premia)", "PivotalPath Global Macro: Risk Premia Index", "GBMRPM", "PivotalPath"),
    ("Global Stock / Bond Momentum", "Newfound/ReSolve Robust Equity Momentum TR Index", "NRROMOT", "Newfound Research; ReSolve Asset Management"),
    ("Risk-Weighted Gold/Bitcoin", "Kaiko ByteTree BOLD1 Inverse Volatility Index", "BOLD1", "ByteTree/Kaiko"),
    ("Cash", "Bloomberg US Treasury Bill Total Return Index Unhedged USD", "LD12TRUU", "Bloomberg"),
    ("Futures Yield (Carry)", "ReSolve Futures Yield Liquid Universe Index", "N/A", "ReSolve Asset Management"),
]

special_notes = {
    "Futures Yield (Carry)": "inception date: 5/30/2024; all data prior to that date is backtested",
}

ticker_info = {}
for widget_name, full_name, ticker, provider in mapping:
    ticker_info[widget_name] = {
        "fullName": full_name,
        "ticker": ticker,
        "provider": provider,
        "specialNote": special_notes.get(widget_name, ""),
    }

with open("data/ticker_info.json", "w") as f:
    json.dump(ticker_info, f, indent=2)

print(f"Created data/ticker_info.json with {len(ticker_info)} entries")
