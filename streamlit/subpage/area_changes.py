import streamlit as st
from streamlit_folium import folium_static
import folium
from io import BytesIO
import json
import os
import ee  
import geemap
from datetime import datetime, timedelta 
import time_func
import ts_trend_analysis_func
from cal_size_func import get_s2_sr_cld_col, apply_cld_shdw_mask, add_cloud_bands, add_shadow_bands, add_cld_shdw_mask, process_cal_size_1
# Define key application functions.
def app():

    # Google Earth Engine Initialization
    ee.Initialize()

    # VWorld map settings
    vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API key
    layer = "Satellite" # VWorld layer
    tileType = "jpeg" # Tile type
    
    def create_folium_map(processed_image, aoi):
        # GEE 이미지를 Folium 지도에 추가
        Map = geemap.Map()
        visualization_params = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 0.3,
            'gamma': 1.4
        }
        Map.addLayer(processed_image, visualization_params, 'Processed Image')
        Map.centerObject(aoi, zoom=10)
        return Map
    
    # Page layout settings
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    
    with col0:
        st.title("🗺️ 면적변화확인") 
        st.write("---"*20) # A dividing line
        if st.toggle("사용설명서"):
            st.write("""
     dfsdfasdfasdf
                     """)

    # 'aoi.geojson' file load
    with open('aoi.geojson', 'r', encoding="utf-8") as ff:
        geojson_data = json.load(ff)

    # Importing a list of local names from a GeoJSON file.
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # Add a new option to the drop-down list.

    # Dividing sections.
    empty1, col1, col2, col3,empty2 = st.columns([0.1,0.4,0.4, 0.2, 0.1])

    # Area Of Interest initialization
    aoi = None

    # Input section
    with col3:
        with st.form("조건 폼"):
            # Select Area of Interest
            selected_name = st.selectbox("관심영역 선택 :", area_names)
            
            # Enable file upload function when '새로운 관심영역 넣기' is selected.
            if selected_name == "새로운 관심영역 넣기":
                uploaded_file = st.file_uploader("GeoJSON 파일을 업로드하세요", type=['geojson'])
                if uploaded_file is not None:
                    aoi = json.load(uploaded_file)
            else:
                # Select an existing AOI.
                aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)

            # select start_data and end_date
            start_date = st.date_input('시작날짜 (2015.05 ~) :',time_func.one_year_ago_f_t()) # Default: Today - one month
            end_date = st.date_input('끝날짜 (~ 오늘) :')
        
            # 입력된 날짜에서 연월 추출
            st_year = start_date.year
            st_month = start_date.month
            en_year = end_date.year
            en_month = end_date.month
            
            # 해당 월의 첫째 날과 마지막 날 계산
            st_date_f = datetime(st_year, st_month, 1)
            st_date_l = datetime(st_year, st_month + 1, 1) - timedelta(days=1)
            en_date_f = datetime(en_year, en_month, 1)
            en_date_l = datetime(en_year, en_month + 1, 1) - timedelta(days=1)

            # 일자 범위를 문자열 형식으로 변환
            st_date_f_str = st_date_f.strftime('%Y-%m-%d')
            st_date_l_str = st_date_l.strftime('%Y-%m-%d')
            en_date_f_str = en_date_f.strftime('%Y-%m-%d')
            en_date_l_str = en_date_l.strftime('%Y-%m-%d')     

            # Run Analysis button.
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")
        
             
    # Visualization section
    with col1:
        st.write("1번 사진 시각화")
        aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)

        s2_sr_first_img = process_cal_size_1(st_date_f_str, st_date_l_str, aoi).first()
        
        location = aoi.centroid().coordinates().getInfo()[::-1]
        # Folium 지도 생성 및 구성
        folium_map = folium.Map(location=location, zoom_start=14)
        folium_map.add_ee_layer(s2_sr_first_img, {
                        'bands': ['B4', 'B3', 'B2'],  # RGB 밴드 선택
                        'min': 0,  # 최소값
                        'max': 1,  # 최대값
                        'gamma': 1  # 대비 조절 (gamma = 1은 기본값)
                    }, 
                    'Processed First Image')

        # Streamlit에서 지도 표시
        folium_static(folium_map)
        
        
        
    with col2: 
        st.write("2번 사진 시각화")

# ---------------------------- Result Screen ---------------------------


    # # Graph section
    # if proceed_button:
    #     # Page layout settings
    #     empty1, col4, empty2 = st.columns([0.12,0.8, 0.12])
        
    #     with col4:
    #         st.write("-----"*20)
    #         st.markdown("""
    #         <h3 style='text-align: center; font-size: 35px;'>⬇️  면적변화 결과  ⬇️</h3>
    #         """, unsafe_allow_html=True)
    #         st.write('')
    #         st.write('')
    #         with st.spinner("변화탐지 분석중"):
                                        
    #             col5,col6 = st.columns(["0.6,0.4"])
    #             with col5:
    #                 col7, col8 = st.columns([0.5,0.5])
    #                 # Extract and display the date of image.
    #                 im1_date = ee.Image(ffa_fl).date().format('YYYY-MM-dd').getInfo()
    #                 im2_date = ee.Image(ffb_fl).date().format('YYYY-MM-dd').getInfo()
                    
    #                 with col7:
    #                     st.write(f"Before : {im1_date}")
    #                 with col8 : 
    #                     st.write(f"After : {im2_date}")
                        
    #                 # side by side    
    #                 st.write("사이드바이 사이드로 전년 당해 보여주기")
                
    #             with col6 :
    #                 st.write("데이터프레임과 그래프")                

# launch
if __name__  == "__main__" :
    app()
    
    