import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from io import BytesIO
import json
import os

def app():
    # 페이지 레이아웃 설정
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("🗺️ 지도확인")
        st.write("---" * 20)

        # VWorld 지도 설정
        vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API 키
        layer = "Satellite" # VWorld 레이어
        tileType = "jpeg" # 타일 유형

        # 관심영역 파일 경로 설정
        geojson_path = 'aoi.geojson'

        # 관심영역 데이터 불러오기 또는 초기화
        if os.path.exists(geojson_path):
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        else:
            geojson_data = {"type": "FeatureCollection", "features": []}

        # 관심영역 이름 목록 추출
        aoi_names = [feature["properties"]["name"] for feature in geojson_data["features"]]


        st.subheader("AOI 조회 및 시각화")
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        
        m = folium.Map(location=[36.6384, 127.6961], zoom_start=7,tiles=tiles, attr=attr)
        folium.TileLayer(
        tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
        attr='VWorld Hybrid',
        name='VWorld Hybrid',
        overlay=True
        ).add_to(m)
        selected_aoi_name = st.selectbox('관심 영역을 선택하세요:', aoi_names)
        selected_aoi = next((feature for feature in geojson_data["features"]
                            if feature["properties"]["name"] == selected_aoi_name), None)
        
        if st.button('관심 영역 조회'):
        # 선택된 관심 지역이 있을 경우에만 해당 지역 폴리곤 표시
            if selected_aoi:
                folium.GeoJson(
                    selected_aoi,
                    name=selected_aoi_name,
                    style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}
                ).add_to(m)
                # 지도를 선택된 폴리곤에 맞게 조정
                m.fit_bounds(folium.GeoJson(selected_aoi).get_bounds())

            else:
                st.error("선택된 관심 영역을 찾을 수 없습니다.")
            # Streamlit 앱에 지도 표시

        folium_static(m)



# launch
if __name__  == "__main__" :
    app()
    
    