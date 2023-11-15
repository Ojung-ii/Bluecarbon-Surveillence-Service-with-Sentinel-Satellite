import streamlit as st

def app():
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
        

# launch
if __name__  == "__main__" :
    app()