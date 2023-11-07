import streamlit as st


def launch() :

    
    st.set_page_config(page_title='국립공원공단 SAR 변화탐지 서비스', page_icon="🛰️", layout='centered', initial_sidebar_state='auto')
    st.title("🛰️ 국립공원공단 SAR 변화탐지 서비스")
    st.write("-------"*20)
    with st.sidebar:
        # 전달.
        api_key = st.text_input("Enter token", value='anything~', placeholder="Enter google earth engine toekn", type="password")
        
        proceed_button = st.button('Proceed',use_container_width=True)
        
        
    # 로컬 파일 시스템에서 GIF 파일 경로 설정
    video_file = '/Users/o_jungii/Bigleader/project/qgis/streamlit/landsat_timelaps.mp4'

    st.video(video_file)
        
# launch
if __name__  == "__main__" :
    launch()

