import streamlit as st
import ee
# Logo settings
def app():
    # Dividing sections
    empty1,col1,col2,col3,col4,empty2 = st.columns([0.5,0.3,0.3,0.3,0.3,0.5], gap="small")
    
    with col1: # KNPS Logo
        st.image("streamlit/logo/knps_logo.png")
    with col2: # BigLeader Logo
        st.image("streamlit/logo/bigleader_logo.png")
    with col3: # Google Logo
        st.image("streamlit/logo/google_logo.png")
    with col4: # Meta Logo
        st.image("streamlit/logo/meta_logo.png")


    # Logo timelapse
    empty3,col5,empty4 = st.columns([0.3,0.5,0.3])
    with col5 : 
        st.image("streamlit/logo/bluecheck_mainpage_logo.gif",  use_column_width="always")

# launch
if __name__  == "__main__" :
    app()