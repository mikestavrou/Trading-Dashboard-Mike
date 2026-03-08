import PIL.Image
from utils import extract_ticker_from_image
import os
from dotenv import load_dotenv

load_dotenv("/Users/mikestavrou/Desktop/ANTIGRAVITY/TRADING DASHBOARD MIKE/.env")

img = PIL.Image.new('RGB', (100, 100), color = 'red')
print(extract_ticker_from_image(img, debug=True))
import streamlit as st
try:
    print(st.session_state.get('ocr_debug_text', 'No debug text'))
except Exception as e:
    print(e)
