import streamlit as st
# import geopandas as gpd
import json

st.set_page_config(page_title="변화탐지_예측", page_icon="👀")
st.title("변화탐지 예측")
st.write("---"*20)

# 'aoi.geojson' 파일을 불러옵니다.
with open('aoi.geojson', 'r', encoding= "utf-8") as f:
    geojson_data = json.load(f)

# 모든 지역 이름을 추출합니다.
area_names = [feature['properties']['name'] for feature in geojson_data['features']]

# Streamlit 드롭다운을 만들고 사용자로부터 선택을 받습니다.
selected_name = st.selectbox("관심 지역을 선택하세요:", area_names)

# 선택된 이름에 해당하는 GeoJSON 데이터를 찾습니다.
aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)
