import PIL.Image
from utils import extract_ticker_from_image
import os
from dotenv import load_dotenv

load_dotenv("/Users/mikestavrou/Desktop/ANTIGRAVITY/TRADING DASHBOARD MIKE/.env")

img = PIL.Image.new('RGBA', (100, 100), color = 'red')
try:
    print("Testing RGBA...")
    print(extract_ticker_from_image(img, debug=True))
except Exception as e:
    print(f"FAILED: {e}")
