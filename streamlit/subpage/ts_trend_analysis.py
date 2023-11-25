import streamlit as st
import folium
from streamlit_folium import folium_static
import json
import ts_trend_analysis_func
import datetime
# VWorld 지도 설정
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API 키
layer = "Satellite" # VWorld 레이어
tileType = "jpeg" # 타일 유형

def app():
    # 페이지 레이아웃 설정
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("📈 식생지수 시계열 경향성 분석") # 페이지 제목
        st.write("---"*20) # 구분선
        on =  st.toggle('사용설명서')

        if on:
            st.write("""
                    식생지수 시계열 경향성 분석을 위한 Streamlit 웹 애플리케이션 입니다.

                        1. 관심 지역 설정
                        2. 분석 기간 설정
                        3. 분석 실행
                        4. 식생지수 선택 및 분석 결과 확인
                            각 식생지수(RVI, NDVI, WAVI, DIFF_BG, WEVI, WTDVI)에 대한 탭을 클릭하여 해당 지수의 분석 결과를 확인합니다.
                            그래프: 선택한 식생지수의 시계열 데이터와 Prophet에 의한 예측 결과를 그래프로 확인합니다.
                            최대값 및 최소값: 해당 지수의 최대값과 최소값이 발생한 날짜를 확인합니다.
                            계절별 및 연간 경향성: 계절별 및 연간 식생지수의 평균값을 확인하여 시간에 따른 변화를 파악합니다.
                    """)

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

    # 관심 지역 목록
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # 드롭다운 목록에 새 옵션 추가

    # 섹션 나누기
    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])

    # aoi 초기화
    aoi = None

    # 오른쪽 섹션: 입력 선택
    with col2:
        with st.form("조건 폼"):
            
            # 관심 지역 선택
            selected_name = st.selectbox("관심지역 선택 :", area_names)
            
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
            start_date = st.date_input('시작날짜 (2015.05 ~) :',datetime.date(2017, 1, 1)).strftime('%Y-%m-%d') 
            end_date = st.date_input('끝날짜 (~ 오늘) :').strftime('%Y-%m-%d') # 디폴트: 오늘 날짜
            
            # 분석 실행 버튼
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")
        
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
        folium.TileLayer(
            tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
            attr='VWorld Hybrid',
            name='VWorld Hybrid',
            overlay=True
        ).add_to(m)
        folium.LayerControl().add_to(m)

        # Streamlit 앱에 지도 표시
        folium_static(m, width=600)

# ------------------------결과------------------------------------
    # 페이지 레이아웃 설정
    if proceed_button:
        st.write("-----"*20)
        st.markdown("""
            <h3 style='text-align: center; font-size: 30px;'>⬇️ 식생지수 시계열 경향성 분석 결과 ⬇️</h3>
            """, unsafe_allow_html=True)
        st.write('')
        st.write('')
        
        # 각각의 식생지수 결과를 볼 수 있는 Expander 생성
        expander_rvi = st.expander("레이더 식생지수 분석결과", expanded=False)
        expander_ndvi = st.expander("광학 식생지수 분석결과", expanded=False)
        # expander_wavi = st.expander("WAVI(물조정) 분석결과", expanded=False)
        # expander_diff_bg = st.expander("DIFF_BG 분석결과", expanded=False)
        expander_wevi = st.expander("광학 식생지수(물 특화) 분석결과", expanded=False)
        # expander_wtdvi = st.expander("WTDVI 분석결과", expanded=False)
        
        # Earth Engine에서 관심 지역을 가져오고 Prophet을 사용하여 시계열 분석 실행 및 결과 플로팅
        parse_aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)

        # RVI
        with expander_rvi:
            st.markdown("""
                <h3 style='text-align: center; font-size: 30px;'>레이더 식생지수</h3>
                """, unsafe_allow_html=True)
            df = ts_trend_analysis_func.calculateRVI(parse_aoi,start_date,end_date)
            forecast,forecast_df,df,m = ts_trend_analysis_func.prophet_process(df)
            fig2 = m.plot_components(forecast)
            ts_trend_analysis_func.plotly(df,forecast)
            # 시계열 결과 플로팅
            st.pyplot(fig2)

        # NDVI
        with expander_ndvi:
            st.markdown("""
                <h3 style='text-align: center; font-size: 30px;'>광학 식생지수</h3>
                """, unsafe_allow_html=True)
            df2 = ts_trend_analysis_func.calculateNDVI(parse_aoi,start_date,end_date)
            forecast2,forecast_df2,df2,m2 = ts_trend_analysis_func.prophet_process(df2)
            fig22 = m2.plot_components(forecast2)
            ts_trend_analysis_func.plotly(df2,forecast2)
            
            # 시계열 결과 플로팅
            st.pyplot(fig22)

        # WAVI
        # with expander_wavi:
        #     st.markdown("""
        #         <h3 style='text-align: center; font-size: 30px;'>WAVI</h3>
        #         """, unsafe_allow_html=True)
        #     df3 = ts_trend_analysis_func.calculateWAVI(parse_aoi,start_date,end_date)
        #     forecast3,forecast_df3,df3,m3 = ts_trend_analysis_func.prophet_process(df3)
        #     fig222 = m3.plot_components(forecast3)
        #     ts_trend_analysis_func.plotly(df3,forecast3)
            
        #     # 시계열 결과 플로팅
        #     st.pyplot(fig222)

        # DIFF_BG    
        # with expander_diff_bg:
        #     st.markdown("""
        #         <h3 style='text-align: center; font-size: 30px;'>expander_diff_bg</h3>
        #         """, unsafe_allow_html=True)
        #     df4 = ts_trend_analysis_func.calculateDIFF_BG(parse_aoi,start_date,end_date)
        #     forecast4,forecast_df3,df4,m4 = ts_trend_analysis_func.prophet_process(df4)
        #     fig4 = m4.plot_components(forecast4)
        #     ts_trend_analysis_func.plotly(df4,forecast4)
            
        #     # 시계열 결과 플로팅
        #     st.pyplot(fig4)

        # WEVI
        with expander_wevi:
            st.markdown("""
                <h3 style='text-align: center; font-size: 30px;'>광학 식생지수(물 특화)</h3>
                """, unsafe_allow_html=True)
            df5 = ts_trend_analysis_func.calculate_WEVI(parse_aoi,start_date,end_date)
            forecast5,forecast_df3,df5,m5 = ts_trend_analysis_func.prophet_process(df5)
            fig5 = m5.plot_components(forecast5)
            ts_trend_analysis_func.plotly(df5,forecast5)
            # lst = ts_trend_analysis_func.ts_analysis(forecast)
            # st.write(lst[0])
            # st.write(lst[1])
            # st.write(lst[2])
            # st.write(lst[3])
            # st.write(lst[4])
            # st.write(lst[5])

            # # 시계열 결과 플로팅
            # st.pyplot(fig5)

        # # WTDVI
        # with expander_wtdvi:
        #     st.markdown("""
        #         <h3 style='text-align: center; font-size: 30px;'>expander_wtdvi</h3>
        #         """, unsafe_allow_html=True)
        #     df6 = ts_trend_analysis_func.calculate_WTDVI(parse_aoi,start_date,end_date)
        #     forecast6,forecast_df3,df6,m6 = ts_trend_analysis_func.prophet_process(df6)
        #     fig6 = m6.plot_components(forecast6)
        #     ts_trend_analysis_func.plotly(df6,forecast6)
            
        #     # 시계열 결과 플로팅
        #     st.pyplot(fig6)      

# launch
if __name__  == "__main__" :
    app()
