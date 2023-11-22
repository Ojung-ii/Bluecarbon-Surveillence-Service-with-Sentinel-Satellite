import streamlit as st
from streamlit_option_menu import option_menu

# 서브 페이지 임포트
from subpage import home, timelapse, check_changes, check_ts_changes, ts_trend_analysis, aoi_revision


def launch() :
    # ---------------------------------- 홈 뼈대 ----------------------------------
    st.set_page_config(page_title='국립공원공단 SAR 변화탐지 서비스', page_icon="🛰️", layout='wide', initial_sidebar_state='collapsed')
    
        # 제목
    st.markdown("""
        <h1 style='text-align: center; font-size: 100px;'>🛰️ SBS SERVICE 🛰️</h1>
        """, unsafe_allow_html=True)
    # 부제목
    st.markdown("""
        <h3 style='text-align: center; font-size: 30px;'> SAR를 활용한 블루카본 변화탐지 서비스 </h3>
        """, unsafe_allow_html=True)
    
    st.write("-------"*20)


    # ------------------------------- 메인 네비게이터 --------------------------------
    # 옵션 메뉴 
    v_menu = ["홈", "타입랩스", "변화탐지 확인", "시계열 변화탐지 확인", "시계열 경향성 분석", "관심영역 추가"]

    selected = option_menu(
        menu_title=None,
        options=v_menu,
        icons=['house', 'camera-video', "search","clock-history","graph-up", 'pin-map'],
        menu_icon="menu-down",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "1px", "border": "2px solid #f0f6fb"},
            "icon": {"color": "navy", "font-size": "20px", "margin-right": "10px"},
            "nav-link": {"font-size": "16px", "color": "navy", "background-color": "#f0f6fb",
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
    if selected == "관심영역 추가":
        aoi_revision.app()               


# launch
if __name__  == "__main__" :
    launch()

