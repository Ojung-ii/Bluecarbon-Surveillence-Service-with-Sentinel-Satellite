import streamlit as st
from streamlit_option_menu import option_menu
import ee
# import sub_page
from subpage import home, timelapse, check_changes, check_ts_changes, ts_trend_analysis, aoi_revision, area_changes
import ee
from google.auth import compute_engine


def launch() :
    service_account = 'national-project@gunwo3442.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, 'gunwo3442-fa3b2b566e8d.json')
    # Earth Engine 초기화
    ee.Initialize(credentials)
# ---------------------------------- Home ----------------------------------
    st.set_page_config(page_title='국립공원공단 SAR 변화탐지 서비스', page_icon="🛰️", layout='wide', initial_sidebar_state='collapsed')
    
    # tile
    # st.markdown("""
    #     <h1 style='text-align: center; font-size: 100px;'>🛰️ BLUE CHECK 🛰️</h1>
    #     """, unsafe_allow_html=True)
    empty1, title, empty2 = st.columns([0.4,0.6,0.4])
    with title :
        st.image("logo/bluecheck_title_logo.png")
    # sub_title
    st.markdown("""
        <h3 style='text-align: center; font-size: 30px;'> 위성영상을 활용한 블루카본 변화탐지 서비스 </h3>
        """, unsafe_allow_html=True)
    
    st.write("-------"*20)
    
    with st.sidebar: 
        st.write("아래버튼을 클릭하여 Google Earth Engine 인증을 갱신해주세요.")
        auth = st.button('Google Earth Engine 인증 갱신버튼')
        


    # ------------------------------- main navigator -------------------------------- 
    v_menu = ["홈", "타입랩스", "변화탐지 확인", "시계열 변화탐지 확인", "시계열 경향성 분석", "면적변화 확인","관심영역 추가"]

    selected = option_menu(
        menu_title=None,
        options=v_menu,
        icons=['house', 'camera-video', "search","clock-history","graph-up", "vr", 'pin-map'],
        menu_icon="menu-down",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "1px", "border": "2px solid #f0f6fb"},
            "icon": {"color": "navy", "font-size": "18px", "margin-right": "5px"},
            "nav-link": {"font-size": "14px", "color": "navy", "background-color": "#f0f6fb",
                         "--hover-color": "#f2f2f2",  "font-weight": "bold", "margin": "2 0px"},
            "nav-link-selected": {"background-color": "#accbea", "color": "navy", "border": "2px solid"}
        }
        )
    if selected == "홈":
        home.app()
    if selected == "타입랩스":
        timelapse.app()
    if selected == "변화탐지 확인":
        check_changes.app()
    if selected == "시계열 변화탐지 확인":
        check_ts_changes.app()
    if selected == "시계열 경향성 분석":
        ts_trend_analysis.app()
    if selected == "면적변화 확인":
        area_changes.app()
    if selected == "관심영역 추가":
        aoi_revision.app()               



        

# launch
if __name__  == "__main__" :
    launch()

