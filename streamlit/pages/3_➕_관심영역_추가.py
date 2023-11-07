import streamlit as st
import json
import os


# 스트림릿 페이지 설정
st.title("AOI 업데이트")
st.write("---"*20)
# 사용자로부터 AOI 이름 입력 받기
aoi_name = st.text_input("AOI 이름을 입력하세요:")

# # geojson 관심영역 입력 받기
# new_aoi_geojson = st.text_input("AOI의 코드를 입력하세용:")

# 사용자로부터 새로운 영역의 GeoJSON 데이터 입력 받기
new_aoi_geojson = st.text_area("새 AOI의 GeoJSON 데이터를 여기에 붙여넣으세요:")


# 파일 경로 설정
geojson_path = 'aoi.geojson'

# 버튼이 눌렸을 때 실행
if st.button("AOI 추가"):
    
      # 입력값이 비어 있는지 확인
    if not aoi_name:
        st.error("AOI 이름을 입력해야 합니다.")
        st.stop()
    elif not new_aoi_geojson:
        st.error("GeoJSON 데이터를 입력해야 합니다.")
        st.stop()
        
        
    # 사용자가 제공한 GeoJSON 데이터를 파싱
    try:
        new_aoi_data = json.loads(new_aoi_geojson)
    except json.JSONDecodeError:
        st.error("제공된 GeoJSON 데이터가 유효하지 않습니다.")
        st.stop()

    # 'properties' 키에 이름 추가
    new_aoi_data['features']['properties']["name"] =  aoi_name
    new_aoi_data = new_aoi_data['features']
    
    # 기존 aoi.geojson 파일 로드 또는 새 파일 생성
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
    else:
        geojson_data = {"type": "FeatureCollection", "features": []}

    # 새 Feature를 FeatureCollection에 추가
    geojson_data['features'].append(new_aoi_data)

    # 변경된 FeatureCollection을 파일에 저장
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=4)

    st.success(f"'{aoi_name}' AOI가 성공적으로 추가되었습니다.")