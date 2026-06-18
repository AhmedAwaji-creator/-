import streamlit as st
import os

st.set_page_config(
    page_title="نظام إدارة مستودعات الطوارئ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# إزالة كل عناصر Streamlit وجعل النظام يملأ الشاشة كاملاً
st.markdown("""
<style>
* {margin:0!important;padding:0!important;box-sizing:border-box}
html, body {width:100vw!important;height:100vh!important;overflow:hidden!important}
#MainMenu, header, footer, .stDeployButton, .stToolbar,
.stDecoration, [data-testid="stToolbar"],
[data-testid="stHeader"],[data-testid="stStatusWidget"],
section[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
.block-container,.stApp,.main,.css-1y4p8pa,.css-18e3th9{
    padding:0!important;margin:0!important;max-width:100%!important;
    width:100vw!important;height:100vh!important}
iframe{
    border:none!important;display:block!important;
    width:100vw!important;height:100vh!important;
    position:fixed!important;top:0!important;left:0!important;
    right:0!important;bottom:0!important;}
div[data-stale="false"] > iframe{width:100vw!important;height:100vh!important}
</style>
""", unsafe_allow_html=True)

html_file = os.path.join(os.path.dirname(__file__), "index.html")
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=1080, scrolling=False)
