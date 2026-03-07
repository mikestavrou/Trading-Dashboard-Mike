import streamlit as st
import os
from datetime import datetime
from werkzeug.utils import secure_filename

UPLOAD_DIR = "uploads"

def inject_custom_css():
    """Injects custom CSS to give the dashboard a premium, dark-mode terminal feel."""
    st.markdown("""
        <style>
            /* Hide Streamlit components */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Custom typography */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            html, body, [class*="css"]  {
                font-family: 'Inter', sans-serif;
            }
            
            /* Premium button styling */
            .stButton > button {
                background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
                color: white !important;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0, 210, 255, 0.15);
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 210, 255, 0.3);
                border: none;
            }
            
            /* Clean Metric cards */
            div[data-testid="metric-container"] {
                background-color: #161b22;
                border: 1px solid #30363D;
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            
            /* Expander styling */
            .streamlit-expanderHeader {
                background-color: #161b22 !important;
                border-radius: 8px;
            }
            
            /* Container borders */
            div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid #30363D !important;
                border-radius: 12px;
                background-color: #0d1117;
            }
            
            /* Input styling */
            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div {
                background-color: #161b22 !important;
                border-color: #30363D !important;
                color: #E6EDF3 !important;
                border-radius: 8px;
            }
            
            /* Responsive Image constraints */
            img[data-testid="stImage"] {
                max-height: 400px;
                object-fit: contain;
                border-radius: 8px;
                background-color: #0A0C10;
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
