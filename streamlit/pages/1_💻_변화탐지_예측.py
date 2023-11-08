import streamlit as st
import folium
from streamlit_folium import folium_static
import json


# page setting and title
st.set_page_config(page_title="변화탐지_예측", page_icon="👀")
st.title("변화탐지 예측")
st.write("---"*20)


# 'aoi.geojson' file load
with open('aoi.geojson', 'r', encoding= "utf-8") as f:
    geojson_data = json.load(f)

# aoi list
area_names = [feature['properties']['name'] for feature in geojson_data['features']]

# divide section
col1,col2 = st.columns([0.8,0.3])


# right section : choice of input
with col2:
    
    # aoi selection
    selected_name = st.selectbox("관심 지역을 선택하세요:", area_names)

    # choose one aoi
    aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)

    # select date
    start_date = st.date_input('시작날짜 선택하세요:') # 디폴트로 오늘 날짜가 찍혀 있다.
    end_date = st.date_input('끝날짜 선택하세요:') # 디폴트로 오늘 날짜가 찍혀 있다.


# left section : visualize mapping with polygon
with col1:
    # 지도 초기화 (대한민국 중심 위치로 설정)
    m = folium.Map(location=[36.5, 127.5], zoom_start=7)
    
   # 선택된 관심 지역이 있을 경우에만 해당 지역 폴리곤 표시
    if aoi:
        folium.GeoJson(
            aoi,
            name=selected_name,
            style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}
        ).add_to(m)
        # 지도를 선택된 폴리곤에 맞게 조정
        m.fit_bounds(folium.GeoJson(aoi).get_bounds())


    # Streamlit 앱에 지도 표시
    folium_static(m)



# 여기는 그래프 넣기
st.write("PETER's CODE HERE for Graph~~~~")