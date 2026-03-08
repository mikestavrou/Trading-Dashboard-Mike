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

            /* Emphasized Form Buttons (Log Activity) */
            div[data-testid="stForm"] .stButton > button {
                animation: pulseBorder 3s infinite;
                border: 1px solid transparent;
            }
            div[data-testid="stForm"] .stButton > button:hover { animation: none; }

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
