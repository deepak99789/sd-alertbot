# ═══════════════════════════════════════════════
#   APNA TOKEN AUR SYMBOLS YAHAN DAALO
# ═══════════════════════════════════════════════

TELEGRAM_TOKEN   = "8781917241:AAFfyCdiJRCx321U_kVp0pJAe1fhKYcS5BU"       # BotFather se mila token
TELEGRAM_CHAT_ID = "513065799"         # @userinfobot se mila ID

# ── Timeframes (minutes mein) ──
TIMEFRAMES = ["15m", "30m", "1h", "2h", "4h", "1d", "1wk"]

# ── Crypto Symbols (Binance) ──
CRYPTO_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"
]

# ── Indian Stocks (NSE) — .NS suffix ──
INDIAN_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "NIFTY50=F", "^NSEI"
]

# ── Forex ──
FOREX_SYMBOLS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X"
]

# ── Pattern Settings ──
LEGIN_BODY_PCT  = 70.0   # Legin candle body >= 70% of range
BASE_BODY_PCT   = 50.0   # Base candle body < 50% of range
LEGOUT_MULT     = 1.0    # Legout body >= Legin body * 1.0

# ── How often to scan (seconds) ──
SCAN_INTERVAL = 60   # har 60 second mein scan
