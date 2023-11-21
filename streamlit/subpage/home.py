import streamlit as st

# 로고 설정
def app():
    # 섹션 나누기
    empty1,col1,col2,col3,col4,empty2 = st.columns([0.5,0.3,0.3,0.3,0.3,0.5], gap="small")
    
    with col1: # 국립공원공단 로고
        st.image("logo/knps_logo.png")
    with col2: # 빅리더 로고
        st.image("logo/bigleader_logo.png")
    with col3: # 구글 로고
        st.image("logo/google_logo.png")
    with col4: # 메타 로고
        st.image("logo/meta_logo.png")


    # 로고 타입랩스
    empty3,col5,empty4 = st.columns([0.3,0.5,0.3])
    with col5 : 
        # 로고 타임랩스 표시
        st.image("logo/mainpage_logo_wh.gif",  use_column_width="always")
        

# launch
if __name__  == "__main__" :
    app()