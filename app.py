import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import time
from datetime import datetime
import threading

# ── Page Config ──
st.set_page_config(page_title="SD Alert Bot", page_icon="📊", layout="centered")

# ── Sidebar Settings ──
st.sidebar.title("⚙️ Bot Settings")
TELEGRAM_TOKEN   = st.sidebar.text_input("Telegram Bot Token", type="password")
TELEGRAM_CHAT_ID = st.sidebar.text_input("Telegram Chat ID")

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Symbols")
crypto_input = st.sidebar.text_area("Crypto (one per line)", "BTC/USDT\nETH/USDT\nSOL/USDT")
stock_input  = st.sidebar.text_area("Stocks/Index (one per line)", "RELIANCE.NS\nTCS.NS\n^NSEI")
forex_input  = st.sidebar.text_area("Forex (one per line)", "EURUSD=X\nGBPUSD=X")

st.sidebar.markdown("---")
st.sidebar.subheader("⏱ Timeframes")
timeframes = st.sidebar.multiselect(
    "Select Timeframes",
    ["15m","30m","1h","2h","4h","1d","1wk"],
    default=["15m","1h","4h","1d"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Pattern Settings")
legin_pct  = st.sidebar.slider("Legin Body % (min)", 50, 95, 70)
base_pct   = st.sidebar.slider("Base Body % (max)",  10, 70, 50)
legout_mul = st.sidebar.slider("Legout Multiplier",  0.5, 3.0, 1.0, 0.1)

# ── Main UI ──
st.title("📊 Supply & Demand Alert Bot")
st.markdown("**Free | No TradingView Premium | 24/7 Telegram Alerts**")
st.markdown("---")

# ── Status ──
status_box  = st.empty()
log_box     = st.empty()
alert_count = st.empty()

# ── Session State ──
if "running"        not in st.session_state: st.session_state.running        = False
if "alerted"        not in st.session_state: st.session_state.alerted        = set()
if "active_zones"   not in st.session_state: st.session_state.active_zones   = {}
if "logs"           not in st.session_state: st.session_state.logs           = []
if "alert_count"    not in st.session_state: st.session_state.alert_count    = 0

# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════
def candle_body(row):  return abs(row["Close"] - row["Open"])
def candle_range(row): return row["High"] - row["Low"]
def body_pct(row):
    r = candle_range(row)
    return candle_body(row) / r * 100 if r != 0 else 0
def is_bull(row): return row["Close"] >= row["Open"]
def is_bear(row): return row["Close"] <  row["Open"]
def bbhigh(row):  return max(row["Open"], row["Close"])
def bblow(row):   return min(row["Open"], row["Close"])

def detect_patterns(df, legin_pct, base_pct, legout_mul):
    patterns = []
    if len(df) < 3:
        return patterns
    lookback = min(50, len(df) - 2)
    for i in range(lookback, 0, -1):
        if i - 2 < 0: continue
        lg  = df.iloc[-i]
        bs  = df.iloc[-(i-1)]
        lo  = df.iloc[-(i-2)]
        if not (body_pct(lg) >= legin_pct and body_pct(bs) < base_pct and candle_body(lo) >= candle_body(lg) * legout_mul):
            continue
        if   is_bull(lg) and is_bull(lo): pat, zt, ep, sl = "RBR", "DEMAND", bblow(bs),  bbhigh(bs)
        elif is_bull(lg) and is_bear(lo): pat, zt, ep, sl = "RBD", "SUPPLY", bbhigh(bs), bblow(bs)
        elif is_bear(lg) and is_bear(lo): pat, zt, ep, sl = "DBD", "SUPPLY", bbhigh(bs), bblow(bs)
        elif is_bear(lg) and is_bull(lo): pat, zt, ep, sl = "DBR", "DEMAND", bblow(bs),  bbhigh(bs)
        else: continue
        patterns.append({"pattern": pat, "zone_type": zt, "entry": round(ep,6),
                         "sl": round(sl,6), "zone_high": round(bs["High"],6),
                         "zone_low": round(bs["Low"],6), "legout_time": str(lo.name)})
    return patterns

def fetch_yf(symbol, tf):
    period_map = {"15m":"5d","30m":"10d","1h":"30d","2h":"60d","4h":"60d","1d":"1y","1wk":"5y"}
    try:
        df = yf.Ticker(symbol).history(period=period_map.get(tf,"30d"), interval=tf)
        return df[["Open","High","Low","Close","Volume"]] if not df.empty else None
    except: return None

def fetch_crypto_yf(symbol, tf):
    sym = symbol.replace("/","-")
    return fetch_yf(sym, tf)

def send_telegram(token, chat_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except: pass

def pat_msg(symbol, tf, p):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (f"{e} <b>{p['pattern']} Pattern Formed!</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Symbol    : <b>{symbol}</b>\n"
            f"⏱ Timeframe : <b>{tf}</b>\n"
            f"🎯 Zone      : <b>{p['zone_type']}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📍 Entry     : <b>{p['entry']}</b>\n"
            f"🛑 SL        : <b>{p['sl']}</b>\n"
            f"📦 Zone      : {p['zone_low']} — {p['zone_high']}")

def retest_msg(symbol, tf, p, price):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (f"⚡ <b>{p['pattern']} RETEST!</b>\n"
            f"📊 {symbol} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"📍 Entry : <b>{p['entry']}</b>\n"
            f"🛑 SL    : <b>{p['sl']}</b>\n"
            f"{e} Price entered <b>{p['zone_type']}</b> zone!")

def sl_msg(symbol, tf, p, price):
    return (f"❌ <b>{p['pattern']} Zone INVALIDATED</b>\n"
            f"📊 {symbol} | {tf}\n"
            f"💰 Price : <b>{price}</b>\n"
            f"🛑 SL Hit: <b>{p['sl']}</b>")

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{ts}] {msg}")
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[:50]

# ══════════════════════════════════════════
# SCAN FUNCTION
# ══════════════════════════════════════════
def scan_all(token, chat_id, crypto_syms, stock_syms, forex_syms, tfs, lp, bp, lm):
    all_markets = [(crypto_syms,"crypto"),(stock_syms,"stock"),(forex_syms,"forex")]
    for symbols, mtype in all_markets:
        for symbol in symbols:
            if not symbol.strip(): continue
            for tf in tfs:
                try:
                    df = fetch_crypto_yf(symbol, tf) if mtype=="crypto" else fetch_yf(symbol, tf)
                    if df is None or len(df) < 5: continue
                    patterns = detect_patterns(df, lp, bp, lm)
                    cur = round(df["Close"].iloc[-1], 6)
                    for p in patterns:
                        pk = f"{symbol}_{tf}_{p['legout_time']}_{p['pattern']}"
                        zk = f"{symbol}_{tf}_{p['legout_time']}"
                        if pk not in st.session_state.alerted:
                            st.session_state.alerted.add(pk)
                            st.session_state.active_zones[zk] = {**p, "symbol": symbol, "tf": tf}
                            send_telegram(token, chat_id, pat_msg(symbol, tf, p))
                            st.session_state.alert_count += 1
                            add_log(f"✅ {p['pattern']} {symbol} {tf}")
                        if zk in st.session_state.active_zones:
                            z   = st.session_state.active_zones[zk]
                            bull = z["zone_type"] == "DEMAND"
                            slk  = zk + "_sl"
                            rtk  = zk + "_retest"
                            if (bull and cur < z["sl"]) or (not bull and cur > z["sl"]):
                                if slk not in st.session_state.alerted:
                                    st.session_state.alerted.add(slk)
                                    send_telegram(token, chat_id, sl_msg(symbol, tf, z, cur))
                                    del st.session_state.active_zones[zk]
                                    add_log(f"❌ SL Hit {symbol} {tf}")
                            elif rtk not in st.session_state.alerted:
                                if (bull and cur <= z["entry"]) or (not bull and cur >= z["entry"]):
                                    st.session_state.alerted.add(rtk)
                                    send_telegram(token, chat_id, retest_msg(symbol, tf, z, cur))
                                    add_log(f"⚡ Retest {symbol} {tf}")
                    time.sleep(0.3)
                except Exception as e:
                    add_log(f"⚠️ Error {symbol} {tf}: {str(e)[:40]}")

# ══════════════════════════════════════════
# START / STOP BUTTONS
# ══════════════════════════════════════════
col1, col2 = st.columns(2)
start_btn = col1.button("▶️ Start Bot",  type="primary", use_container_width=True)
stop_btn  = col2.button("⏹ Stop Bot",   type="secondary", use_container_width=True)

if start_btn:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        st.error("❌ Pehle Telegram Token aur Chat ID daalo (sidebar mein)!")
    elif not timeframes:
        st.error("❌ Kam se kam ek timeframe select karo!")
    else:
        st.session_state.running = True
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                      "🤖 <b>SD Alert Bot Started!</b>\nMonitoring all markets... 📊")
        add_log("🚀 Bot started!")

if stop_btn:
    st.session_state.running = False
    add_log("⏹ Bot stopped.")

# ══════════════════════════════════════════
# BOT LOOP
# ══════════════════════════════════════════
if st.session_state.running:
    status_box.success("🟢 Bot Running... Telegram pe alerts aa rahe hain!")
    alert_count.metric("Total Alerts Sent", st.session_state.alert_count)

    crypto_syms = [s.strip() for s in crypto_input.split("\n") if s.strip()]
    stock_syms  = [s.strip() for s in stock_input.split("\n")  if s.strip()]
    forex_syms  = [s.strip() for s in forex_input.split("\n")  if s.strip()]

    with st.spinner("🔍 Scanning markets..."):
        scan_all(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                 crypto_syms, stock_syms, forex_syms,
                 timeframes, legin_pct, base_pct, legout_mul)

    log_box.text_area("📋 Activity Log", "\n".join(st.session_state.logs), height=300)
    alert_count.metric("Total Alerts Sent", st.session_state.alert_count)
    time.sleep(60)
    st.rerun()

else:
    status_box.warning("🔴 Bot Stopped. Start karo!")
    if st.session_state.logs:
        log_box.text_area("📋 Activity Log", "\n".join(st.session_state.logs), height=300)

st.markdown("---")
st.caption("Made with ❤️ | Supply & Demand Zone Bot | Free Forever")
