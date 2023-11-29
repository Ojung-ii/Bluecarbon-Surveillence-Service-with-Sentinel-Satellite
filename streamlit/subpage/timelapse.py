import streamlit as st
import geemap
import ee
from timelapse_func import create_sentinel1_timelapse, create_sentinel2_timelapse
import json
from ts_trend_analysis_func import create_ee_polygon_from_geojson
import datetime
import time_func
# Google Earth Engine initialization
ee.Initialize()

def app():
     # Page layout settings
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title('👀 타임랩스 생성기') 
        st.markdown("""
            <h3 style='text-align: left; font-size: 22px;'>( sentinel-1 & 2 : 레이더 및 광학 위성영상 활용 )</h3>
            """, unsafe_allow_html=True)
        st.write("---"*20) 
        if st.toggle("사용설명서"):
            st.write("""
                    타임랩스 기능 사용설명서
                    
                        1. 데이터셋 및 관심 영역 선택
                        2. 분석 기간 및 주기 설정
                        3. 타임랩스 생성 버튼 클릭
                        4. 결과 확인

                        * 주의사항 : 인터넷 연결 상태에 따라 타임랩스 생성 시간이 달라질 수 있습니다.
                     """)

    # 'aoi.geojson' file load
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Importing a list of local names from a GeoJSON file.
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # using new aoi 

    # Dividing sections
    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])

    # Explain section
    with col1:
        st.write(" 오른쪽의 옵션을 선택하고 '타임랩스 생성' 버튼을 누르면 타임랩스가 나와요. 👉🏻")

    # Input section
    with col2:
        with st.form("조건 폼"):
            # User's Input
            # Select type of satellite
            dataset = st.selectbox('위성영상 선택 :', ['Sentinel-1(레이더)', 'Sentinel-2(광학)'])
            selected_name = st.selectbox("관심영역 선택 :", area_names)

            # Date Settings
            start_date = st.date_input('시작날짜 (2015.05 ~) :',time_func.one_year_ago_f_t()) # Default: today - one year
            end_date = st.date_input('끝날짜 (~ 오늘) :')# Default: today

            # Select cycle 
            frequency_options = {'일': 'day', '월': 'month', '분기': 'quarter', '연': 'year'}
            frequency_label = st.selectbox('빈도 선택 : ', options=list(frequency_options.keys()))
            frequency = frequency_options[frequency_label]

            # Enable file upload function when '새로운 관심영역 넣기' is selected.
            if selected_name == "새로운 관심영역 넣기":
                uploaded_file = st.file_uploader("GeoJSON 파일을 업로드하세요", type=['geojson'])
                if uploaded_file is not None:
                    aoi = json.load(uploaded_file)
            else:
                # Select an existing AOI.
                aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)
                
                aoi = create_ee_polygon_from_geojson(aoi)

            # Use the 'strftime' function to convert the date to a format of 'YYYYMMDD' that is compatible with the gemap function.
            formatted_start_date = start_date.strftime('%Y%m%d') # Correctly formatted as 'YYYYMMDD'
            formatted_end_date = end_date.strftime('%Y%m%d') # Correctly formatted as 'YYYYMMDD'

            # Run Analysis button.
            st.write("")
            proceed_button = st.form_submit_button("☑️ 타임랩스 생성")


# ------------------------- Result Screen --------------------------
    with col1:
        if proceed_button:

            with st.spinner('타임랩스를 생성하는 중입니다...'):
                output_gif = './timelapse.gif'  # Path and file name to store the created timelapse
                
                # If Sentinel-1 is selected.
                if dataset == 'Sentinel-1(레이더)':
                    # Create_sentinel1_timelapse.
                    create_sentinel1_timelapse(aoi, formatted_start_date, formatted_end_date, frequency, output_gif)    
                    st.image(output_gif, caption=f'{dataset} 타임랩스', use_column_width=True)
                
                # If Sentinel-2 is selected.
                elif dataset == 'Sentinel-2(광학)':
                    # Create_sentinel2_timelapse.
                    create_sentinel2_timelapse(aoi, formatted_start_date, formatted_end_date, frequency, output_gif)
                    st.image(output_gif, caption=f'{dataset} 타임랩스', use_column_width=True ) 
                # GIF 파일 로드 함수
                def load_gif(gif_path):
                    with open(gif_path, "rb") as file:
                        return file.read()

                # 파일을 다운로드 버튼으로 제공
                st.download_button(
                    label="타임랩스 다운로드",
                    data=load_gif('./timelapse.gif'),
                    file_name='timelapse.gif',
                    mime="image/gif"
                )
# launch
if __name__  == "__main__" :
    app()