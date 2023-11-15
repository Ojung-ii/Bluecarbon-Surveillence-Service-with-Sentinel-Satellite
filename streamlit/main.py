import streamlit as st
from streamlit_option_menu import option_menu

# 서브 페이지 임포트
from pages import 타임랩스 #, 2_💻_변화탐지_확인


def launch() :

    st.set_page_config(page_title='국립공원공단 SAR 변화탐지 서비스', page_icon="🛰️", layout='wide', initial_sidebar_state='collapsed')
    
        # 제목
    st.markdown("""
        <h1 style='text-align: center; font-size: 100px;'>🛰️ SBS SERVICE </h1>
        """, unsafe_allow_html=True)
    # 부제목
    st.markdown("""
        <h3 style='text-align: center; font-size: 30px;'> SAR를 활용한 블루카본 변화탐지 서비스 </h3>
        """, unsafe_allow_html=True)
    
    st.write("-------"*20)



    # 옵션 메뉴 
    v_menu = ["Home", "Timelapse", "Change_detection"]

    selected = option_menu(
        menu_title="페이지 이름들",
        options=v_menu,
        icons=None,
        menu_icon="menu-down",
        default_index=0,
        orientation="horizontal"
        )
    if selected == "Home":

        
        # 로고 이미지들 
        empty1,col1,col2,col3,col4,empty2 = st.columns([0.5,0.3,0.3,0.3,0.3,0.5], gap="small")
        
        with col1:
            st.image("logo/knps_logo.png")
        with col2:
            st.image("logo/bigleader_logo.png")
        with col3:
            st.image("logo/google_logo.png")
        with col4:
            st.image("logo/meta_logo.png")


        # 로고 타입랩스
        empty3,col5,empty4 = st.columns([0.3,0.5,0.3])
        with col5 : 
            # 타임랩스 로고 표시
            st.image("logo/mainpage_logo_wh.gif",  use_column_width="always")
            
    if selected == "Timelapse":
        타임랩스.app()
        
  
# launch
if __name__  == "__main__" :
    launch()

