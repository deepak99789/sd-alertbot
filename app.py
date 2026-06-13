import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="SD Zone Scanner", page_icon="📊", layout="wide")

NIFTY100 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","NESTLEIND.NS","BAJFINANCE.NS",
    "HCLTECH.NS","POWERGRID.NS","NTPC.NS","TECHM.NS","ONGC.NS",
    "TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","BAJAJFINSV.NS","COALINDIA.NS",
    "JSWSTEEL.NS","GRASIM.NS","DIVISLAB.NS","DRREDDY.NS","EICHERMOT.NS",
    "CIPLA.NS","BPCL.NS","TATACONSUM.NS","BRITANNIA.NS","APOLLOHOSP.NS",
    "HEROMOTOCO.NS","HINDALCO.NS","INDUSINDBK.NS","SBILIFE.NS","HDFCLIFE.NS",
    "BAJAJ-AUTO.NS","TATASTEEL.NS","UPL.NS","SHREECEM.NS","PIDILITIND.NS",
    "DMART.NS","HAVELLS.NS","BERGEPAINT.NS","DABUR.NS","MARICO.NS",
    "MCDOWELL-N.NS","COLPAL.NS","SIEMENS.NS","ADANIGREEN.NS","ADANITRANS.NS",
    "BOSCHLTD.NS","ICICIGI.NS","ICICIPRULI.NS","GODREJCP.NS","PAGEIND.NS",
    "TORNTPHARM.NS","LUPIN.NS","BIOCON.NS","AUROPHARMA.NS","CONCOR.NS",
    "NMDC.NS","VEDL.NS","SAIL.NS","INDUSTOWER.NS","DLF.NS",
    "AMBUJACEM.NS","ACC.NS","BANKBARODA.NS","PNB.NS","CANBK.NS",
    "FEDERALBNK.NS","IDFCFIRSTB.NS","PERSISTENT.NS","MPHASIS.NS","COFORGE.NS",
    "LTIM.NS","OFSS.NS","ZOMATO.NS","NYKAA.NS","POLICYBZR.NS",
    "IRCTC.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","BAJAJHLDNG.NS","MOTHERSON.NS",
    "ASHOKLEY.NS","TVSMOTOR.NS","BALKRISIND.NS","JUBLFOOD.NS","^NSEI","^BSESN"
]
US100 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","NFLX",
    "AMD","PEP","ADBE","QCOM","CSCO","TXN","AMAT","INTU","ISRG","AMGN",
    "MU","LRCX","KLAC","REGN","PANW","ADI","SNPS","CDNS","MRVL","CRWD",
    "FTNT","ORLY","ADP","MNST","CTAS","PAYX","MELI","WDAY","ODFL","FAST",
    "ROST","BIIB","IDXX","TEAM","CPRT","EA","ZS","DDOG","NET","SNOW",
    "PLTR","COIN","RBLX","ABNB","DASH","UBER","SHOP","SQ","PYPL","INTC",
    "ORCL","CRM","NOW","VEEV","HUBS","MDB","SPY","QQQ","DIA","IWM"
]
FOREX = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","USDCHF=X","AUDUSD=X","USDCAD=X","NZDUSD=X",
    "EURGBP=X","EURJPY=X","EURCHF=X","EURAUD=X","EURCAD=X","EURNZD=X",
    "GBPJPY=X","GBPCHF=X","GBPAUD=X","GBPCAD=X","GBPNZD=X",
    "AUDJPY=X","AUDCHF=X","AUDCAD=X","AUDNZD=X",
    "CADJPY=X","CADCHF=X","NZDJPY=X","NZDCHF=X","NZDCAD=X","CHFJPY=X",
    "USDINR=X","USDSGD=X","USDMXN=X","USDZAR=X"
]
COMMODITY = ["GC=F","SI=F","CL=F","BZ=F","NG=F","HG=F"]
CRYPTO    = ["BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD"]

NAME_MAP = {
    "GC=F":"XAUUSD","SI=F":"XAGUSD","CL=F":"WTI_OIL","BZ=F":"BRENT",
    "NG=F":"NAT_GAS","HG=F":"COPPER","BTC-USD":"BTCUSD","ETH-USD":"ETHUSD",
    "BNB-USD":"BNBUSD","SOL-USD":"SOLUSD","XRP-USD":"XRPUSD",
    "^NSEI":"NIFTY50","^BSESN":"SENSEX","SPY":"SP500","QQQ":"NASDAQ",
    "DIA":"DOW","IWM":"RUSSELL"
}
def dn(s): return NAME_MAP.get(s, s.replace(".NS","").replace("=X","").replace("-USD","USD").replace("=F",""))

PERIOD_MAP = {"5m":"1d","15m":"2d","30m":"5d","75m":"5d","125m":"5d",
              "1h":"7d","2h":"10d","4h":"15d","5h":"20d","6h":"20d",
              "8h":"30d","10h":"30d","16h":"40d","1d":"60d","1wk":"1y"}
FETCH_MAP  = {"5m":"5m","15m":"15m","30m":"30m","75m":"15m","125m":"5m",
              "1h":"1h","2h":"1h","4h":"1h","5h":"1h","6h":"1h",
              "8h":"1h","10h":"1h","16h":"1h","1d":"1d","1wk":"1wk"}
RESAMP_MAP = {"75m":"75T","125m":"125T","2h":"2h","4h":"4h","5h":"5h",
              "6h":"6h","8h":"8h","10h":"10h","16h":"16h"}

def body(r):    return abs(r["Close"]-r["Open"])
def rng(r):     return r["High"]-r["Low"]
def bpct(r):    return body(r)/rng(r)*100 if rng(r)!=0 else 0
def is_bull(r): return r["Close"]>=r["Open"]
def bbhigh(r):  return max(r["Open"],r["Close"])
def bblow(r):   return min(r["Open"],r["Close"])

def resample(df, rule):
    return df.resample(rule).agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

def fetch_df(sym, tf):
    try:
        ft = FETCH_MAP.get(tf, tf)
        pr = PERIOD_MAP.get(tf, "7d")
        df = yf.Ticker(sym).history(period=pr, interval=ft)
        if df.empty: return None
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        rs = RESAMP_MAP.get(tf)
        if rs: df = resample(df, rs)
        return df if len(df) >= 5 else None
    except: return None

def calc_proximal_distal(bs, zt):
    base_bull = is_bull(bs)
    if zt == "DEMAND":
        proximal = bbhigh(bs) if base_bull else bs["Open"]
        distal   = bs["Low"]
    else:
        proximal = bblow(bs) if not base_bull else bs["Open"]
        distal   = bs["High"]
    return round(proximal, 6), round(distal, 6)

def detect(df, legin_pct):
    """
    Correct detection using forward indexing.
    df.iloc[0] = oldest candle
    df.iloc[-1] = latest candle
    Legin at lg_idx, Base(s) after, Legout(s) after base.
    Returns LATEST pattern with most legouts.
    """
    if len(df) < 5: return None
    n = len(df)
    results = []

    for lg_idx in range(0, n-3):
        lg = df.iloc[lg_idx]
        if bpct(lg) < legin_pct: continue
        lb      = body(lg)
        lg_bull = is_bull(lg)

        for bc in [1, 2, 3]:
            # Base candles: lg_idx+1 to lg_idx+bc
            base_end = lg_idx + bc
            if base_end >= n - 1: break

            bases = [df.iloc[lg_idx + 1 + b] for b in range(bc)]
            # All base candles body <= legin body * 0.5
            if not all(body(b) <= lb * 0.5 for b in bases): continue

            # First legout
            lo1_idx = base_end + 1
            if lo1_idx >= n: break
            lo1 = df.iloc[lo1_idx]

            # Legout1: body >= legin body, same direction
            if body(lo1) < lb: continue
            if lg_bull and not is_bull(lo1): continue
            if not lg_bull and is_bull(lo1): continue

            lc = 1
            # Legout2: same direction only
            if lo1_idx + 1 < n:
                lo2 = df.iloc[lo1_idx + 1]
                if (lg_bull and is_bull(lo2)) or (not lg_bull and not is_bull(lo2)):
                    lc = 2
                    # Legout3: same direction only
                    if lo1_idx + 2 < n:
                        lo3 = df.iloc[lo1_idx + 2]
                        if (lg_bull and is_bull(lo3)) or (not lg_bull and not is_bull(lo3)):
                            lc = 3

            # Pattern type
            if   lg_bull and is_bull(lo1):      pat, zt = "RBR", "DEMAND"
            elif lg_bull and not is_bull(lo1):  pat, zt = "RBD", "SUPPLY"
            elif not lg_bull and not is_bull(lo1): pat, zt = "DBD", "SUPPLY"
            else:                               pat, zt = "DBR", "DEMAND"

            bs       = bases[0]
            prox, dist = calc_proximal_distal(bs, zt)
            bhi = max(b["High"] for b in bases)
            blo = min(b["Low"]  for b in bases)

            results.append({
                "pattern"     : pat,
                "zone_type"   : zt,
                "proximal"    : prox,
                "distal"      : dist,
                "zone_high"   : round(bhi, 4),
                "zone_low"    : round(blo, 4),
                "base_count"  : bc,
                "legout_count": lc,
                "strength"    : "🟡 Good" if lc==1 else "🟠 Very Good" if lc==2 else "🌟 The Best",
                "base_color"  : "🟢 Green" if is_bull(bs) else "🔴 Red",
                "status"      : "✅ FRESH",
                "lo1_idx"     : lo1_idx,
                "lg_idx"      : lg_idx,
            })

    if not results: return None
    # Keep latest pattern (highest lo1_idx), break ties by most legouts
    results.sort(key=lambda x: (x["lo1_idx"], x["lc"]), reverse=True)
    best = results[0]
    best.pop("lo1_idx"); best.pop("lg_idx")
    return best

def send_telegram(token, chat_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                     json={"chat_id":chat_id,"text":text,"parse_mode":"HTML"}, timeout=10)
    except: pass

def tg_msg(sym, tf, p):
    e = "🟢" if p["zone_type"]=="DEMAND" else "🔴"
    return (f"{e} <b>{p['pattern']} Pattern!</b>\n"
            f"📊 <b>{dn(sym)}</b> | ⏱ {tf}\n"
            f"💪 {p['strength']} | B:{p['base_count']} L:{p['legout_count']}\n"
            f"🎯 {p['zone_type']} | {p['status']}\n"
            f"🕯 Base: {p['base_color']}\n"
            f"📍 Proximal: <b>{p['proximal']}</b>  ← Entry\n"
            f"📏 Distal  : <b>{p['distal']}</b>    ← SL")

# ══════════════════════════════════
# UI
# ══════════════════════════════════
st.markdown("""
<style>
.main-title{text-align:center;font-size:2.5rem;font-weight:800;
    background:linear-gradient(90deg,#00C853,#FFD600);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sub{text-align:center;color:#aaa;margin-bottom:1rem;}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Supply & Demand Zone Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Multi-Market | Multi-Timeframe | Telegram Alerts</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("🔔 Telegram")
    tg_token   = st.text_input("Bot Token", type="password")
    tg_chat_id = st.text_input("Chat ID")
    send_tg    = st.checkbox("Send to Telegram", value=True)
    st.markdown("---")
    st.subheader("🎯 Pattern Settings")
    legin_pct = st.slider("Legin Body % (min)", 50, 95, 70)
    st.markdown("---")
    st.subheader("🔍 Filters")
    zone_status = st.multiselect("Zone Status", ["✅ FRESH","🔁 TESTED"], default=["✅ FRESH","🔁 TESTED"])
    zone_types  = st.multiselect("Zone Type",   ["DEMAND","SUPPLY"],     default=["DEMAND","SUPPLY"])
    strength_f  = st.multiselect("Strength",    ["🟡 Good","🟠 Very Good","🌟 The Best"], default=["🟡 Good","🟠 Very Good","🌟 The Best"])

col1, col2 = st.columns([1,1])
with col1:
    st.subheader("📈 Select Markets")
    mkt_indian = st.checkbox("🇮🇳 Indian Stocks (Nifty 100)", value=True)
    mkt_us     = st.checkbox("🇺🇸 US Stocks (Top 100)",       value=False)
    mkt_forex  = st.checkbox("💱 Forex (Major+Minor+Cross)",  value=False)
    mkt_comm   = st.checkbox("🏅 Commodities (Gold,Silver...)",value=False)
    mkt_crypto = st.checkbox("₿ Crypto",                      value=False)
    st.subheader("⏱ Timeframes")
    all_tfs = ["5m","15m","30m","75m","125m","1h","2h","4h","5h","6h","8h","10h","16h","1d","1wk"]
    sel_tfs = st.multiselect("Select Timeframes", all_tfs, default=["15m","1h","4h","1d"])

with col2:
    st.subheader("✏️ Custom Symbols")
    custom_input = st.text_area("Add custom symbols (comma separated)", placeholder="AAPL, BTCUSD, EURUSD=X")
    st.subheader("📊 Scan Info")
    info_box = st.empty()

st.markdown("---")
scan_btn = st.button("🔍 Scan Now", type="primary", use_container_width=True)
progress_bar = st.empty()
status_text  = st.empty()

if scan_btn:
    symbols = []
    if mkt_indian: symbols += [(s,"🇮🇳 Indian") for s in NIFTY100]
    if mkt_us:     symbols += [(s,"🇺🇸 US")      for s in US100]
    if mkt_forex:  symbols += [(s,"💱 Forex")    for s in FOREX]
    if mkt_comm:   symbols += [(s,"🏅 Commodity") for s in COMMODITY]
    if mkt_crypto: symbols += [(s,"₿ Crypto")   for s in CRYPTO]
    if custom_input.strip():
        for s in custom_input.split(","):
            s=s.strip()
            if s: symbols.append((s,"✏️ Custom"))

    tfs = sel_tfs if sel_tfs else ["15m","1h","4h"]

    if not symbols:
        st.warning("⚠️ Koi market select nahi ki!")
    else:
        total   = len(symbols) * len(tfs)
        done    = 0
        results = []
        info_box.info(f"📊 Scanning {len(symbols)} symbols × {len(tfs)} timeframes = {total} combinations")

        for sym, market in symbols:
            for tf in tfs:
                done += 1
                pct = int(done/total*100)
                progress_bar.progress(pct)
                status_text.text(f"🔍 Scanning {dn(sym)} | {tf} ({done}/{total})")
                try:
                    df = fetch_df(sym, tf)
                    if df is None: continue
                    p = detect(df, legin_pct)
                    if p is None: continue
                    if p["zone_type"] not in zone_types: continue
                    if p["strength"]  not in strength_f: continue
                    if p["status"]    not in zone_status: continue
                    cur = round(df["Close"].iloc[-1], 4)
                    results.append({
                        "Market"       : market,
                        "Asset"        : dn(sym),
                        "Timeframe"    : tf,
                        "Pattern"      : p["pattern"],
                        "Zone Type"    : p["zone_type"],
                        "Strength"     : p["strength"],
                        "Base Count"   : p["base_count"],
                        "Legout Count" : p["legout_count"],
                        "Base Color"   : p["base_color"],
                        "Status"       : p["status"],
                        "Proximal"     : p["proximal"],
                        "Distal"       : p["distal"],
                        "Current Price": cur,
                    })
                    if send_tg and tg_token and tg_chat_id:
                        send_telegram(tg_token, tg_chat_id, tg_msg(sym, tf, p))
                        time.sleep(0.3)
                except: pass
                time.sleep(0.15)

        progress_bar.empty()
        status_text.empty()

        if results:
            df_res = pd.DataFrame(results)
            st.success(f"✅ Scan Complete! {len(results)} zones found!")
            st.markdown("### 📋 Zone Results")

            def color_row(row):
                c = "background-color:#1a3a2a" if row["Zone Type"]=="DEMAND" else "background-color:#3a1a1a"
                return [c]*len(row)

            st.dataframe(df_res.style.apply(color_row,axis=1), use_container_width=True, height=500)

            st.markdown("### 📊 Summary")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Zones",   len(results))
            c2.metric("🟢 Demand",     len([r for r in results if r["Zone Type"]=="DEMAND"]))
            c3.metric("🔴 Supply",     len([r for r in results if r["Zone Type"]=="SUPPLY"]))
            c4.metric("🌟 Best Zones", len([r for r in results if r["Strength"]=="🌟 The Best"]))

            csv = df_res.to_csv(index=False)
            st.download_button("⬇️ Download CSV", csv, "sd_zones.csv", "text/csv", use_container_width=True)
        else:
            st.warning("⚠️ Koi zone nahi mila! Filters loose karo ya timeframes badlo.")

st.markdown("---")
st.caption("📊 SD Zone Scanner | Free Forever | No TradingView Premium Needed")
