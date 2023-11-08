import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw

# 스트림릿 앱 초기화
st.title('지도 위에 폴리곤을 그리세요')

# 폴리움 지도 생성
m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

# 폴리움 지도에 그리기 플러그인 추가
draw = Draw(export=True)
m.add_child(draw)
st.write(draw.last_draw)
# 스트림릿에 지도 표시
folium_static(m)

# 사용자가 폴리곤을 그리고 'Save Polygon' 버튼을 클릭하면 스트림릿이 폴리곤 데이터를 처리
if st.button('Save Polygon'):
    # NOTE: 여기에는 폴리움 지도에서 폴리곤 데이터를 추출하고
    # 스트림릿의 세션 상태에 저장하는 실제 코드가 필요합니다.
    # 이 기능을 구현하는 것은 스트림릿과 자바스크립트의 상호작용을 필요로 하며,
    # 이는 스트림릿의 표준 기능 범위를 벗어납니다.
    pass

# 폴리곤 시각화 버튼
if st.button('Visualize Polygon'):
    if 'geojson' in st.session_state:
        # 세션 상태에서 폴리곤 데이터 불러오기
        stored_geojson = st.session_state['geojson']

        # 시각화를 위한 새로운 폴리움 지도 객체 생성
        m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

        # 스타일 함수 정의
        def style_function(feature):
            return {
                'fillColor': '#ffaf00',
                'color': 'blue',
                'weight': 2,
                'dashArray': '5, 5'
            }

        # GeoJSON 레이어 추가 및 스타일 적용
        folium.GeoJson(
            stored_geojson,
            style_function=style_function,
            name='geojson'
        ).add_to(m)

        # 스트림릿에서 지도 표시
        folium_static(m)
    else:
        st.error("No polygon data to visualize.")
