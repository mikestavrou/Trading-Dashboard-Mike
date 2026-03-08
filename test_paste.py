import streamlit as st
from streamlit_paste_button import paste_image_button

st.write("Test Paste Button")
paste_result = paste_image_button("Paste Here", key="test_paste")

if paste_result.image_data is not None:
    st.write("Image pasted successfully!")
    st.image(paste_result.image_data)
