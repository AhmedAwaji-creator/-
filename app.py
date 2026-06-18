import streamlit as st
import os

st.set_page_config(
    page_title="نظام إدارة مستودعات الطوارئ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu, header, footer, .stDeployButton, .stToolbar,
.stDecoration, [data-testid="stToolbar"],
[data-testid="stHeader"], [data-testid="stStatusWidget"],
section[data-testid="stSidebar"] {display:none!important}
.block-container {padding:0!important;max-width:100%!important;margin:0!important}
.stApp {overflow:hidden!important}
.stApp > div {padding:0!important;margin:0!important}
iframe {border:none!important;display:block!important;
        position:fixed!important;top:0!important;left:0!important;
        width:100vw!important;height:100vh!important}
</style>
""", unsafe_allow_html=True)

html_file = os.path.join(os.path.dirname(__file__), "index.html")
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=900, scrolling=False)
