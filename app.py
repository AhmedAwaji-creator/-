import streamlit as st
import os
import time

st.set_page_config(
    page_title="نظام إدارة مستودعات الطوارئ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
* {margin:0!important;padding:0!important;box-sizing:border-box}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{
    width:100vw!important;height:100vh!important;overflow:hidden!important}
#MainMenu,header,footer,.stDeployButton,.stToolbar,
[data-testid="stToolbar"],[data-testid="stHeader"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{display:none!important}
.block-container,.main{
    padding:0!important;margin:0!important;
    max-width:100vw!important;width:100vw!important;height:100vh!important}
iframe{
    border:none!important;display:block!important;
    width:100vw!important;height:100vh!important;
    position:fixed!important;top:0!important;left:0!important;}
</style>
""", unsafe_allow_html=True)

html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# إضافة timestamp لمنع الـ cache
html_content = html_content.replace(
    '</head>',
    f'<!-- cache-bust: {int(time.time())} --></head>',
    1
)

st.components.v1.html(html_content, height=1080, scrolling=False)
