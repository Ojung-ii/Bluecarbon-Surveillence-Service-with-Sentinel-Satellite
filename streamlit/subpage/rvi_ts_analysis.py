import streamlit as st
import folium
from streamlit_folium import folium_static
import json
import sar_func

def app():
    # 페이지 설정과 제목
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("📈 식생지수 시계열 경향성 분석")
        st.write("---"*20)
 

    #Vworld
    vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
    layer = "Satellite"
    tileType = "jpeg"

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

    # 관심 지역 목록
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # 드롭다운 목록에 새 옵션 추가

    # 섹션 나누기
    empty1, col1, col2, empty2 = st.columns([0.1,0.7, 0.4, 0.1])

    # aoi 초기화
    aoi = None

    # 오른쪽 섹션: 입력 선택
    with col2:
        # 관심 지역 선택
        selected_name = st.selectbox("관심 지역을 선택하세요:", area_names)
        
        # '새로운 관심영역 넣기'가 선택되면 파일 업로드 기능 활성화
        if selected_name == "새로운 관심영역 넣기":
            uploaded_file = st.file_uploader("GeoJSON 파일을 업로드하세요", type=['geojson'])
            if uploaded_file is not None:
                # 파일 읽기
                aoi = json.load(uploaded_file)
        else:
            # 기존 관심 지역 선택
            aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)

        # 날짜 선택
        start_date = st.date_input('시작날짜 선택하세요:').strftime('%Y-%m-%d')   # 디폴트로 오늘 날짜가 찍혀 있다.
        end_date = st.date_input('끝날짜 선택하세요:').strftime('%Y-%m-%d')     # 디폴트로 오늘 날짜가 찍혀 있다.

        
        # 분석 실행 버튼
        st.write("")
        proceed_button = st.button("☑️ 분석 실행")
        
    # 왼쪽 섹션: 폴리곤 매핑 시각화
    with col1:
        # 지도 초기화 (대한민국 중심 위치로 설정)
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        m = folium.Map(location=[36.5, 127.5], zoom_start=10,tiles=tiles, attr=attr)

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



    if proceed_button:
        st.write("-----"*20)
        st.markdown("""
            <h3 style='text-align: center; font-size: 30px;'>⬇️ 식생지수 시계열 경향성 분석 결과 ⬇️</h3>
            """, unsafe_allow_html=True)
        st.write('')
        st.write('')
        
        # tab1, tab2 = st.tabs(["RVI", "NDVI"])
        expander_rvi = st.expander("RVI(SAR) 분석결과", expanded=False)
        expander_ndvi = st.expander("NDVI(광학) 분석결과", expanded=False)
        parse_aoi = sar_func.create_ee_polygon_from_geojson(aoi)
        start_date = '2017-01-01'
        end_date = '2023-03-01'

        with expander_rvi:
            st.markdown("""
                <h3 style='text-align: center; font-size: 30px;'>RVI</h3>
                """, unsafe_allow_html=True)
            df = sar_func.calculateRVI(parse_aoi,start_date,end_date)
            forecast,forecast_df,df,m = sar_func.prophet_process(df)
            sar_func.plotly(df,forecast)
            fig2 = m.plot_components(forecast)

            # Display the modified components plot using st.pyplot()
            st.pyplot(fig2)
        with expander_ndvi:
            st.markdown("""
                <h3 style='text-align: center; font-size: 30px;'>NDVI</h3>
                """, unsafe_allow_html=True)
            df2 = sar_func.calculateNDVI(parse_aoi,start_date,end_date)
            forecast2,forecast_df2,df2,m2 = sar_func.prophet_process(df2)
            sar_func.plotly(df2,forecast2)
            fig22 = m2.plot_components(forecast2)
            # Display the modified components plot using st.pyplot()
            st.pyplot(fig22)

# launch
if __name__  == "__main__" :
    app()
