import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from io import BytesIO
import json
import os

def app():
    # 스트림릿 페이지 설정
    st.title("AOI 업데이트")
    st.write("---" * 20)

    #Vworld
    vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
    layer = "Satellite"
    tileType = "jpeg"

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

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["AOI 조회", "신규 AOI 추가", "AOI 제거"])

    # AOI 조회 탭
    with tab1:
        st.subheader("AOI 조회 및 시각화")
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"

        m = folium.Map(location=[36.6384, 127.6961], zoom_start=7,tiles=tiles, attr=attr)
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
    # 신규 AOI 추가 탭
    with tab2:
        st.subheader("신규 AOI 추가")
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"

        m = folium.Map(location=[36.6384, 127.6961], zoom_start=7)

        # 폴리움 지도에 그리기 플러그인 추가
        draw = Draw(export=True)
        m.add_child(draw)
        # 스트림릿에 지도 표시
        folium_static(m)
        new_aoi_name = st.text_input("AOI 이름을 입력하세요:")
        new_aoi_file = st.file_uploader("새로운 관심영역의 파일을 업로드하세요", type=["geojson"])
        if st.button("AOI 추가"):
            if not new_aoi_name:
                st.error("AOI 이름을 입력해야 합니다.")
            elif not new_aoi_file:
                st.error("새로운 관심영역 파일을 업로드해야 합니다.")
            else:
                new_aoi_data = json.load(BytesIO(new_aoi_file.getvalue()))
                new_aoi_data["features"][0]["properties"]["name"] = new_aoi_name
                geojson_data['features'].append(new_aoi_data["features"][0])
                with open(geojson_path, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, ensure_ascii=False, indent=4)
                st.success(f"'{new_aoi_name}' 이름으로 AOI가 성공적으로 추가되었습니다.")
                aoi_names.append(new_aoi_name)  # 업데이트된 aoi_names 리스트

    # AOI 제거 탭
    with tab3:
        st.subheader("AOI 제거")
        selected_aoi_name_to_remove = st.selectbox('제거할 관심 영역을 선택하세요:', ["선택하세요..."] + aoi_names)
        if st.button('AOI 제거') and selected_aoi_name_to_remove != "선택하세요...":
            geojson_data["features"] = [feature for feature in geojson_data["features"]
                                        if feature["properties"]["name"] != selected_aoi_name_to_remove]
            with open(geojson_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=4)
            st.success(f"'{selected_aoi_name_to_remove}' 이름의 AOI가 성공적으로 제거되었습니다.")
            aoi_names.remove(selected_aoi_name_to_remove)  # 업데이트된 aoi_names 리스트
            
            
# launch
if __name__  == "__main__" :
    app()