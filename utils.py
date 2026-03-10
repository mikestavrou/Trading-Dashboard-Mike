import streamlit as st
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from google import genai
from dotenv import load_dotenv
import re

load_dotenv()

UPLOAD_DIR = "uploads"

def inject_custom_css():
    """Injects high-end, premium glassmorphic CSS to completely overhaul the UI."""
    st.markdown("""
        <style>
            /* Reset & Hide defaults */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Typography & Core Background (Animated Mesh Gradient) */
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@500;700&display=swap');
            
            @keyframes gradientBG {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            .stApp {
                background: linear-gradient(-45deg, #0f172a, #020617, #1e1b4b, #09090b);
                background-size: 400% 400%;
                animation: gradientBG 20s ease infinite;
                font-family: 'Outfit', sans-serif;
                color: #f8fafc;
            }
            
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif;
            }
            
            h1, h2, h3 {
                font-family: 'Space Grotesk', sans-serif !important;
                background: linear-gradient(to right, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            }

            /* Global Animations */
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes pulseBorder { 0% { border-color: rgba(56, 189, 248, 0.3); } 50% { border-color: rgba(129, 140, 248, 0.8); box-shadow: 0 0 15px rgba(129, 140, 248, 0.4); } 100% { border-color: rgba(56, 189, 248, 0.3); } }

            .main .block-container { 
                max-width: 2000px !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                animation: fadeIn 0.8s ease forwards; 
            }
            div[data-testid="stVerticalBlock"] > div { 
                animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
                opacity: 0;
            }
            div[data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay: 0.1s; }
            div[data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.2s; }
            div[data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.3s; }

            /* Premium Glassmorphic Containers */
            div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(15, 23, 42, 0.4) !important;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 16px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
                padding: 10px;
            }
            
            div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                border-color: rgba(56, 189, 248, 0.4) !important;
                transform: translateY(-2px);
                box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.15);
            }

            /* Metric Cards as Floating Widgets */
            div[data-testid="metric-container"] {
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.9));
                backdrop-filter: blur(8px);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-left: 4px solid #38bdf8;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            div[data-testid="metric-container"]:hover {
                transform: scale(1.05) translateY(-5px);
                border-left-color: #818cf8;
                box-shadow: 0 15px 30px rgba(129, 140, 248, 0.2);
            }

            /* High-End Inputs & Text Areas */
            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div {
                background: rgba(2, 6, 23, 0.6) !important;
                backdrop-filter: blur(4px);
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                color: #e2e8f0 !important;
                border-radius: 10px;
                padding: 12px !important;
                transition: all 0.3s ease !important;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
            }
            .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus, .stSelectbox > div > div > div:focus {
                border-color: #38bdf8 !important;
                background: rgba(15, 23, 42, 0.8) !important;
                box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2), inset 0 2px 4px rgba(0,0,0,0.1) !important;
            }

            /* Cyberpunk / Action Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
                color: #ffffff !important;
                border: none;
                border-radius: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 10px 24px;
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
                position: relative;
                overflow: hidden;
                z-index: 1;
            }
            .stButton > button::after {
                content: '';
                position: absolute;
                top: 0; left: 0; width: 100%; height: 100%;
                background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
                opacity: 0;
                z-index: -1;
                transition: opacity 0.3s ease;
            }
            .stButton > button:hover {
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
            }
            .stButton > button:hover::after { opacity: 1; }
            .stButton > button:active { transform: translateY(1px); }
            /* TRADE button — kill ALL blue on active/focus, keep dark green */
            div[data-testid="stButton"]:first-of-type > button,
            div[data-testid="stButton"]:first-of-type > button:hover,
            div[data-testid="stButton"]:first-of-type > button:active,
            div[data-testid="stButton"]:first-of-type > button:focus,
            div[data-testid="stButton"]:first-of-type > button:focus-visible,
            div[data-testid="stButton"]:first-of-type > button:focus:not(:focus-visible) {
                background: linear-gradient(135deg, rgba(15,23,42,0.97), rgba(5,46,22,0.65)) !important;
                box-shadow: none !important;
                outline: none !important;
                outline-offset: 0 !important;
                transform: none !important;
                border: 2px solid rgba(34,197,94,0.5) !important;
            }
            div[data-testid="stButton"]:first-of-type > button::after {
                display: none !important;
            }

            /* Emphasized Form Buttons (Log Activity) */
            div[data-testid="stForm"] .stButton > button {
                animation: pulseBorder 3s infinite;
                border: 1px solid transparent;
            }
            div[data-testid="stForm"] .stButton > button:hover { animation: none; }

            /* ── TRADE mega button class (applied by JS in app.py) ── */
            button.trade-mega-btn {
                background: linear-gradient(135deg, rgba(15,23,42,0.97), rgba(5,46,22,0.65)) !important;
                border: 2px solid rgba(34,197,94,0.5) !important;
                border-radius: 20px !important;
                min-height: 155px !important;
                width: 100% !important;
                padding: 20px 0 16px 0 !important;
                box-shadow: 0 0 40px rgba(34,197,94,0.12) !important;
                transition: box-shadow 0.2s ease !important;
                outline: none !important;
                transform: none !important;
            }
            button.trade-mega-btn:hover {
                background: linear-gradient(135deg, rgba(15,23,42,0.97), rgba(5,46,22,0.65)) !important;
                box-shadow: 0 0 65px rgba(34,197,94,0.35) !important;
                border-color: rgba(34,197,94,0.85) !important;
            }
            button.trade-mega-btn:active,
            button.trade-mega-btn:focus,
            button.trade-mega-btn:focus-visible {
                background: linear-gradient(135deg, rgba(15,23,42,0.97), rgba(5,46,22,0.65)) !important;
                box-shadow: 0 0 25px rgba(34,197,94,0.15) !important;
                border-color: rgba(34,197,94,0.6) !important;
                outline: none !important;
                outline-offset: 0 !important;
            }
            button.trade-mega-btn p {
                font-size: 12px !important;
                font-weight: 600 !important;
                letter-spacing: 2.5px !important;
                white-space: pre-line !important;
                line-height: 2.4 !important;
                color: #94a3b8 !important;
            }
            button.trade-mega-btn p::first-line {
                font-size: 44px !important;
                font-weight: 900 !important;
                letter-spacing: 8px !important;
                color: #22c55e !important;
            }

            /* Expander (Glass Accordion) */
            .streamlit-expanderHeader {
                background: rgba(30, 41, 59, 0.4) !important;
                backdrop-filter: blur(6px);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                font-family: 'Space Grotesk', sans-serif;
                font-weight: 600;
                transition: all 0.3s ease !important;
            }
            .streamlit-expanderHeader:hover {
                background: rgba(51, 65, 85, 0.6) !important;
                border-color: rgba(56, 189, 248, 0.3) !important;
            }

            /* Responsive Image constraints */
            div[data-testid="stImage"], div[data-testid="stImage"] img {
                width: 100% !important;
            }
            div[data-testid="stImage"] img {
                height: auto !important;
                object-fit: contain !important;
                max-width: 1100px !important;
                margin: 0 auto !important;
                display: block !important;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 1px solid rgba(255,255,255,0.08);
            }
            div[data-testid="stImage"]:hover img {
                transform: scale(1.03);
                box-shadow: 0 12px 30px rgba(56, 189, 248, 0.2);
                border-color: rgba(56, 189, 248, 0.4);
            }

            /* Tabs */
            button[data-baseweb="tab"] {
                font-family: 'Space Grotesk', sans-serif;
                font-weight: 600;
                color: #94a3b8 !important;
                background: transparent !important;
                border: none !important;
                border-bottom: 2px solid transparent !important;
                transition: all 0.3s ease !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #38bdf8 !important;
                border-bottom: 2px solid #38bdf8 !important;
                text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
            }
            button[data-baseweb="tab"]:hover {
                color: #e2e8f0 !important;
                background: rgba(255, 255, 255, 0.03) !important;
            }
        </style>
    """, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file, prefix=""):
    """
    Saves a Streamlit UploadedFile object to the uploads directory.
    Returns the relative path to the saved file.
    """
    if uploaded_file is None:
        return None
        
    # Ensure the upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Create a safe, unique filename
    original_filename = secure_filename(uploaded_file.name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Construct filename e.g., "trade_20231027_103000_chart.png"
    safe_prefix = secure_filename(prefix) + "_" if prefix else ""
    new_filename = f"{safe_prefix}{timestamp}_{original_filename}"
    
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    # Write the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    return file_path

def save_pil_image(pil_image, prefix=""):
    """
    Saves a PIL Image object to the uploads directory.
    Returns the relative path to the saved file.
    """
    if pil_image is None:
        return None
        
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = secure_filename(prefix) + "_" if prefix else ""
    new_filename = f"{safe_prefix}{timestamp}_pasted.png"
    
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    pil_image.save(file_path, "PNG")
        
    return file_path

def save_audio_file(audio_bytes, prefix=""):
    """
    Saves raw audio bytes from the voice recorder to the uploads directory.
    Returns the relative path to the saved file.
    """
    if audio_bytes is None:
        return None
        
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = secure_filename(prefix) + "_" if prefix else ""
    new_filename = f"{safe_prefix}{timestamp}_voice_note.wav"
    
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
        
    return file_path

def extract_ticker_from_image(pil_image, debug=False):
    """
    Uses Google Gemini Flash Vision API to scan a pasted image and perfectly extract
    the primary ticker symbol (e.g., BTC, AAPL, SOL).
    Returns an empty string if it fails.
    """
    if pil_image is None:
        return ""
        
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            if debug: st.session_state['ocr_debug_text'] = "Error: GEMINI_API_KEY not found in .env file."
            return ""

        client = genai.Client(api_key=api_key)
        
        prompt = (
            "You are a trading assistant. Analyze this trading chart. "
            "Identify the primary asset or ticker symbol being traded (e.g., AAPL, BTC, SOL, NQ). "
            "If it's a forex/crypto pair like BTC/USDT, just return BTC. "
            "Return ONLY the uppercase ticker symbol and nothing else. No explanation."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, pil_image]
        )
        
        text = response.text.strip().upper()
        
        if debug:
            st.session_state['ocr_debug_text'] = f"Gemini RAW Output: {text}"
            
        # Clean up the output just in case it included extra punctuation
        clean_match = re.search(r'([A-Z0-9]{2,10})', text)
        if clean_match:
            return clean_match.group(1)
            
        return text
    except Exception as e:
        if debug:
            st.session_state['ocr_debug_text'] = f"Gemini API Error: {str(e)}"
        return ""

def get_market_condition():
    """
    Fetches REAL Solana DEX volume from DeFiLlama (free, no API key needed).
    Fetches pump.fun graduation rate from Dune Analytics (needs DUNE_API_KEY in .env).
    Returns: (vol_ok, grad_ok, gk_vol_24h, gk_avg_24h, gk_grad, error_msg)
    """
    import requests
    import os

    vol_ok = False
    grad_ok = False
    gk_vol   = 0.0
    gk_avg   = 0.0
    gk_grad  = 0.0
    error_msg = ""

    # ── 1. SOLANA DEX VOLUME — GeckoTerminal h1 (free, no key) ────────────
    # Sum h1 volume across top Solana pools sorted by 24h volume.
    # DeFiLlama still used for total7d → weekly hourly average.
    try:
        import time

        # Step A: DeFiLlama for 7-day total (weekly hourly avg denominator)
        r7d = requests.get(
            "https://api.llama.fi/overview/dexs/solana"
            "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyVolume",
            timeout=12
        )
        total7d  = 0.0
        total24h_fallback = 0.0
        if r7d.status_code == 200:
            d7 = r7d.json()
            total7d  = float(d7.get("total7d")  or 0)
            total24h_fallback = float(d7.get("total24h") or 0)
        gk_avg = round((total7d / 168) / 1_000_000, 2) if total7d else 0.0

        # Step B: GeckoTerminal top pools → sum h1 volumes (true 1-hour data)
        h1_total = 0.0
        gt_ok = False
        for page in range(1, 6):   # pages 1-5 = top ~100 pools by 24h volume
            try:
                gr = requests.get(
                    f"https://api.geckoterminal.com/api/v2/networks/solana/pools"
                    f"?sort=h24_volume_usd_desc&page={page}",
                    headers={"Accept": "application/json;version=20230302"},
                    timeout=10
                )
                if gr.status_code == 200:
                    for pool in gr.json().get("data", []):
                        vol_h1 = pool.get("attributes", {}).get("volume_usd", {}).get("h1", "0")
                        h1_total += float(vol_h1 or 0)
                    gt_ok = True
                elif gr.status_code == 429:
                    error_msg += "GeckoTerminal rate-limited. "
                    break
                time.sleep(0.25)   # be polite to the free API
            except Exception:
                break

        if gt_ok and h1_total > 0:
            gk_vol = round(h1_total / 1_000_000, 2)
            vol_ok = gk_vol > gk_avg
        else:
            # Fallback: DeFiLlama 24h ÷ 24
            gk_vol = round((total24h_fallback / 24) / 1_000_000, 2)
            vol_ok = gk_vol > gk_avg
            error_msg += "GeckoTerminal unavailable — using DeFiLlama 24h estimate. "

    except Exception as e:
        error_msg += f"Volume fetch error: {str(e)[:60]}. "

    # ── 2. PUMP.FUN GRADUATION RATE — Dune query 6375001 (non-blocking) ──────
    # Phase 1 (first call): triggers a fresh Dune execution, returns -2.0 (pending).
    # Phase 2 (after Refresh): checks the stored execution_id for results.
    # This keeps the dashboard from freezing during Dune's 60-90s query time.
    try:
        dune_key = os.getenv("DUNE_API_KEY", "")
        if not dune_key:
            gk_grad = 0.0
            error_msg += "No DUNE_API_KEY in .env — graduation rate unavailable. "
        else:
            DUNE_HEADERS = {"X-DUNE-API-KEY": dune_key}
            # `dune_exec_id` is passed in from session state (None on first run)
            dune_exec_id = os.getenv("_DUNE_EXEC_ID_INTERNAL", "")  # not used — see app.py

            # Try to get latest results directly first (fast path — cached result)
            fast = requests.get(
                "https://api.dune.com/api/v1/query/6375001/results?limit=5",
                headers=DUNE_HEADERS, timeout=10
            )
            if fast.status_code == 200:
                rows = fast.json().get("result", {}).get("rows", [])
                rate = None
                for row in rows:
                    r_val = row.get("Graduation Rate (%)")
                    day_val = row.get("day", "")
                    # Only accept rows from 2026
                    if r_val is not None and "2026" in str(day_val):
                        rate = r_val
                        break
                if rate is not None:
                    gk_grad = round(float(rate), 2)
                    grad_ok = gk_grad > 1.2
                else:
                    # No 2026 data yet → trigger a fresh execution and return pending
                    exec_r = requests.post(
                        "https://api.dune.com/api/v1/query/6375001/execute",
                        headers=DUNE_HEADERS, json={}, timeout=10
                    )
                    gk_grad = -2.0   # sentinel: "execution triggered, check back"
                    if exec_r.status_code == 200:
                        error_msg += f"Dune running (exec {exec_r.json().get('execution_id','?')[:12]}…). Hit Refresh in ~90s. "
                    else:
                        error_msg += "Dune triggered but no 2026 data yet. Hit Refresh soon. "
            else:
                gk_grad = 0.0
                error_msg += f"Dune results HTTP {fast.status_code}. "
    except Exception as e:
        gk_grad = 0.0
        error_msg += f"Graduation rate error: {str(e)[:50]}. "

    return vol_ok, grad_ok, gk_vol, gk_avg, gk_grad, error_msg

def get_wallet_condition(trades_df, max_daily_loss, max_consecutive_losses):
    """
    Evaluates wallet P&L and recent trade history to prevent overtrading.
    Returns: (is_safe: bool, message: str)
    """
    if trades_df.empty:
        return True, "No recent trades. You are safe to start."
        
    # 1. Check Max Daily Loss
    # Get today's trades based on entry_date string matching today
    today_str = datetime.now().date().strftime('%Y-%m-%d')
    todays_trades = trades_df[trades_df['entry_date'] == today_str]
    
    if not todays_trades.empty:
        daily_pnl = todays_trades['pnl'].sum()
        if daily_pnl <= -max_daily_loss:
            return False, f"Daily Loss Limit Reached! (Current PnL: ${daily_pnl:.2f} / Max: -${max_daily_loss:.2f})"
            
    # 2. Check Consecutive Losses (Revenge Trading)
    # The dataframe is already ordered by created_at DESC (newest first)
    if not trades_df.empty:
        # Get the 'pnl' column of the first N trades
        recent_pnls = trades_df['pnl'].head(max_consecutive_losses).tolist()
        
        # Check if we actually have that many trades and ALL of them are negative
        if len(recent_pnls) == max_consecutive_losses and all(pnl < 0 for pnl in recent_pnls):
            return False, f"Revenge Trading Detected! {max_consecutive_losses} consecutive losses."
            
    return True, "Wallet and Risk Limits are Stable."
