import streamlit as st
from streamlit_folium import folium_static

import folium
from folium.plugins import Draw
from io import BytesIO
import json
import os



# 스트림릿 페이지 설정
st.title("AOI 업데이트")
st.write("---"*20)

# ------------------------------신규 aoi 다운 기능 ------------------------------------------
new_aoi_download = st.toggle('신규 aoi 영역지정 및 다운')

if new_aoi_download :
    # 폴리움 지도 생성
    m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

    # 폴리움 지도에 그리기 플러그인 추가
    draw = Draw(export=True)
    m.add_child(draw)

    # 스트림릿에 지도 표시
    folium_static(m)
    
# ------------------------------신규 aoi 추가 기능  ------------------------------------------
# 사용자로부터 AOI 이름 입력 받기
aoi_name = st.text_input("AOI 이름을 입력하세요:")

# geojson 관심영역 입력 받기
new_aoi_file = st.file_uploader("새로운 관심영역의 파일을 업로드하세요", type=["geojson"])

# 업로드된 파일 처리
if new_aoi_file is not None:
    # 파일의 내용을 읽어 파이썬 객체로 변환
    new_aoi_data = json.load(BytesIO(new_aoi_file.getvalue()))
    # 이제 'aoi_data' 변수를 사용하여 필요한 작업을 수행할 수 있습니다.


# 관심영역 파일 경로 설정
geojson_path = 'aoi.geojson'

# 버튼이 눌렸을 때 실행
if st.button("AOI 추가"):
    
      # 입력값이 비어 있는지 확인
    if not aoi_name:
        st.error("AOI 이름을 입력해야 합니다.")
        st.stop()
    elif not new_aoi_file:
        st.error("새로운 관심영역 파일을 업로드해야 합니다.")
        st.stop()
        
   # 업로드한 파일 내용을 처리
    new_aoi_data = json.load(BytesIO(new_aoi_file.getvalue()))
    # 업로드한 GeoJSON에서 첫 번째 Feature의 properties에 이름 추가
    new_aoi_data["features"][0]["properties"]["name"] = aoi_name
    
    # 기존 aoi.geojson 파일 로드 또는 새 파일 생성
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
    else:
        geojson_data = {"type": "FeatureCollection", "features": []}

    # 새 Feature를 FeatureCollection에 추가
    geojson_data['features'].append(new_aoi_data["features"][0])

    # 변경된 FeatureCollection을 파일에 저장
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=4)

    st.success(f"'{aoi_name}' 이름으로 AOI가 성공적으로 추가되었습니다.")
    
    
# ------------------------------ aoi 지도 시각화 기능 ------------------------------------------
# 관심 영역 조회 및 시각화
if st.button('관심 영역 조회'):
    # 저장된 GeoJSON 파일이 존재하는지 확인
    if os.path.exists(geojson_path):
        # 저장된 GeoJSON 파일을 불러옴
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # 관심 영역의 이름을 추출하여 리스트에 저장
        aoi_names = [feature["properties"]["name"] for feature in geojson_data["features"]]
        
        # 드롭다운 메뉴를 통해 사용자에게 관심 영역 선택 요청
        selected_aoi_name = st.selectbox('관심 영역을 선택하세요:', aoi_names)
        
        # 선택된 관심 영역을 찾음
        selected_aoi = next((feature for feature in geojson_data["features"] 
                             if feature["properties"]["name"] == selected_aoi_name), None)
        
        # 선택된 관심 영역이 있으면 지도에 시각화
        if selected_aoi:
            # 폴리움 지도 생성
            m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

            # 선택된 관심 영역의 GeoJSON 레이어 추가
            folium.GeoJson(selected_aoi).add_to(m)

            # 스트림릿에 지도 표시
            folium_static(m)
        else:
            st.error("선택된 관심 영역을 찾을 수 없습니다.")
    else:
        st.error("저장된 GeoJSON 파일이 존재하지 않습니다.")

# ------------------------------ aoi 제거 기능  ------------------------------------------

