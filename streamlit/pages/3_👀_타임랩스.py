import streamlit as st
import geemap
import ee
from timelapse_func import create_sentinel1_timelapse, create_sentinel2_timelapse
import json
from sar_func import create_ee_polygon_from_geojson

# Google Earth Engine 초기화
ee.Initialize()

# Streamlit 앱 제목 설정
st.set_page_config(page_title="변화탐지_확인", page_icon="👀")

st.title('👀 타임랩스 생성기')
st.write("---"*20)
# 날짜 형식 변환 함수
def format_date(date_int):
    date_str = str(date_int)
    # YYYYMMDD 형식의 문자열을 YYYY-MM-DD로 변환
    return f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}'

# 'aoi.geojson' 파일 로드
with open('aoi.geojson', 'r', encoding="utf-8") as f:
    geojson_data = json.load(f)

# 관심 지역 목록
area_names = [feature['properties']['name'] for feature in geojson_data['features']]
area_names.append("새로운 관심영역 넣기")  # 드롭다운 목록에 새 옵션 추가


# User's Input
dataset = st.selectbox('데이터셋 선택', ['Sentinel-1', 'Sentinel-2'])
selected_name = st.selectbox("관심 지역을 선택하세요:", area_names)
start_date = st.text_input('시작 날짜 (YYYYMMDD 형식)', value='20200101')
end_date = st.text_input('종료 날짜 (YYYYMMDD 형식)', value='20200131')
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

# 사용자가 제공한 날짜를 변환
formatted_start_date = format_date(int(start_date))
formatted_end_date = format_date(int(end_date))


if st.button('타임랩스 생성'):
    with st.spinner('타임랩스를 생성하는 중입니다...'):
        output_gif = './timelapse.gif'  # 타임랩스를 저장할 경로와 파일명
        if dataset == 'Sentinel-1':
            create_sentinel1_timelapse(aoi, start_date, end_date, frequency, output_gif)
        elif dataset == 'Sentinel-2':
            create_sentinel2_timelapse(aoi, start_date, end_date, frequency, output_gif)

        st.image(output_gif, caption=f'{dataset} 타임랩스', use_column_width=True)

