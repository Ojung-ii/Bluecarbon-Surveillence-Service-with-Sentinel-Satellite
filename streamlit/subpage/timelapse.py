import streamlit as st
import geemap
import ee
from timelapse_func import create_sentinel1_timelapse, create_sentinel2_timelapse
import json
from sar_func import create_ee_polygon_from_geojson
import datetime

# Google Earth Engine 초기화
ee.Initialize()

def app():
    # Streamlit 앱 제목 설정
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title('👀 타임랩스 생성기')
        st.write("---"*20)

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

    # 관심 지역 목록
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # 드롭다운 목록에 새 옵션 추가

    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])
    with col1:

        st.write(" 타임랩스가 여기에 표시될 예정입니다. 오른쪽의 옵션을 선택하고 '타임랩스 생성' 버튼을 눌러주세요. 👉🏻")

    with col2:
        # User's Input
        dataset = st.selectbox('데이터셋 선택', ['Sentinel-1', 'Sentinel-2'])
        selected_name = st.selectbox("관심 지역을 선택하세요:", area_names)
        # 날짜 선택
        start_date = st.date_input('시작날짜 선택하세요:', datetime.date(2020, 1, 1)) 
        end_date = st.date_input('끝날짜 선택하세요:', datetime.date(2023, 1, 31))
        frequency = st.selectbox('빈도 선택', options=['day', 'month', 'quarter', 'year'])

        # '새로운 관심영역 넣기'가 선택되면 파일 업로드 기능 활성화
        if selected_name == "새로운 관심영역 넣기":
            uploaded_file = st.file_uploader("GeoJSON 파일을 업로드하세요", type=['geojson'])
            if uploaded_file is not None:
                # 파일 읽기
                aoi = json.load(uploaded_file)
        else:
            # 기존 관심 지역 선택
            aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)
            
            aoi = create_ee_polygon_from_geojson(aoi)

        # Use strftime to format the date as 'YYYYMMDD' for compatibility with geemap functions
        formatted_start_date = start_date.strftime('%Y%m%d') # Correctly formatted as 'YYYYMMDD'
        formatted_end_date = end_date.strftime('%Y%m%d') # Correctly formatted as 'YYYYMMDD'

        # 분석 실행 버튼
        st.write("")
        proceed_button = st.button("☑️ 타임랩스 생성")

    with col1:   
        if proceed_button:
            with st.spinner('타임랩스를 생성하는 중입니다...'):
                output_gif = './timelapse.gif'  # 타임랩스를 저장할 경로와 파일명
                if dataset == 'Sentinel-1':
                    # Pass the formatted dates directly to the function
                    create_sentinel1_timelapse(aoi, formatted_start_date, formatted_end_date, frequency, output_gif)    
                    st.image(output_gif, caption=f'{dataset} 타임랩스', use_column_width=True)
                elif dataset == 'Sentinel-2':
                    # Pass the formatted dates directly to the function
                    create_sentinel2_timelapse(aoi, formatted_start_date, formatted_end_date, frequency, output_gif)
                    st.image(output_gif, caption=f'{dataset} 타임랩스', use_column_width=True ) 

# launch
if __name__  == "__main__" :
    app()