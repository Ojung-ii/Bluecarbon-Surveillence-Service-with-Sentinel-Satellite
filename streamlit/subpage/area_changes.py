import streamlit as st
from streamlit_folium import folium_static
import folium
from folium import plugins
from io import BytesIO
import json
import os
import ee  
import geemap
import pandas as pd
from datetime import datetime, timedelta 
import time_func
import ts_trend_analysis_func
from area_changes_func import process_cal_size_1, add_ee_layer, mask_for_aoi,process_image,make_layer,calculate_area,calculate_all_area,define_threshold
# Define key application functions.
def app():

    # Google Earth Engine Initialization
    # ee.Initialize()

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
        st.title("🗺️ 면적변화 확인")
        st.markdown("""
            <h3 style='text-align: left; font-size: 22px;'>( sentinel-2 : 광학 위성영상 활용 )</h3>
            """, unsafe_allow_html=True)
        
        st.write("---"*20) # A dividing line
        if st.toggle("사용설명서"):
            st.write("""
                    면적변화 확인 기능 사용설명서

                        1. 관심 영역 설정
                        2. 날짜 설정
                        3. 임계값 설정 (기본값 1로 설정)
                        4. 분석 실행
                        5. 2개의 side by side 지도 확인
                            1) 2달간의 데이터를 이용하여 구름없는 이미지로 만든 지도
                            2) FAI를 활용하여 잘피가 있는 지역을 색상으로 표현한 지도
                        6. 분석결과 오른쪽의 변화된 면적 수치와 그래프를 통한 확인
                        
                        * 분석결과 맨아래의 FAI지수 통계를 활용하여 임계값 설정에 도움을 받을 수 있습니다.
                     """)

    # 'aoi.geojson' file load
    with open('aoi.geojson', 'r', encoding="utf-8") as ff:
        geojson_data = json.load(ff)

    # Importing a list of local names from a GeoJSON file.
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # Add a new option to the drop-down list.

    # Dividing sections.
    empty1, col1, col2, empty2 = st.columns([0.1,0.7, 0.3, 0.1])

    # Area Of Interest initialization
    aoi = None

    # Input section
    with col2:
        st.write("")
        st.write("")
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

            number = st.number_input('임계값 설정(기본값:1)', value=1)
        
            # 입력된 날짜에서 연월 추출
            st_year = start_date.year
            st_month = start_date.month
            en_year = end_date.year
            en_month = end_date.month
            
            st_date_f = datetime(st_year, st_month, 1)
            en_date_f = datetime(en_year, en_month, 1)
            # 해당 월의 첫째 날과 마지막 날 계산
            if st_month == 12:
                st_date_l = datetime(st_year + 1, 1, 1) - timedelta(days=1)
            else:
                st_date_l = datetime(st_year, st_month + 1, 1) - timedelta(days=1)

            if en_month == 12:
                en_date_l = datetime(en_year + 1, 1, 1) - timedelta(days=1)
            else:
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
        aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)

        s2_sr_first_img = process_cal_size_1(st_date_f_str, st_date_l_str, aoi)
        s2_sr_sec_img = process_cal_size_1(en_date_f_str, en_date_l_str, aoi)
        # Folium 라이브러리의 Map 객체에 위에서 정의한 함수를 추가합니다.1
        folium.Map.add_ee_layer = add_ee_layer
        # Create a folium map object.
        center = aoi.centroid().coordinates().getInfo()[::-1]
        m1 = folium.Map(location=center, zoom_start=12)
        vis_params={'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 2500, 'gamma': 1.1}
        # Add layers to the folium map.

        layer1 = make_layer(s2_sr_first_img,vis_params,'S2 cloud-free mosaic')
        layer2 = make_layer(s2_sr_sec_img,vis_params,'S2 cloud-free mosaic')
        sbs = folium.plugins.SideBySideLayers(layer1, layer2)

        layer1.add_to(m1)
        layer2.add_to(m1)
        sbs.add_to(m1)
        # Add a layer control panel to the map.
        m1.add_child(folium.LayerControl())
        plugins.Fullscreen().add_to(m1)
        folium_static(m1, width = 720)

        
        
        
        
        

# ---------------------------- Result Screen ---------------------------


    # Graph section
    if proceed_button:
        # Page layout settings
        empty1, col4, empty2 = st.columns([0.12,0.8, 0.12])
        
        with col4:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  면적변화 결과  ⬇️</h3>
            """, unsafe_allow_html=True)
            st.write('')
            st.write('')
            with st.spinner("면적변화 분석중"):
                                        
                col5,col6 = st.columns([0.7,0.3])
                with col5:
                    # side by side    
                    fai_s2_sr_sec_img = mask_for_aoi(s2_sr_sec_img, aoi)
                    fai_s2_sr_sec_img_parse = process_image(fai_s2_sr_sec_img)
                    fai_s2_sr_first_img = mask_for_aoi(s2_sr_first_img, aoi)
                    fai_s2_sr_first_img_parse = process_image(fai_s2_sr_first_img)
                    
                    uvi_params = {
                        'bands': ['FAI'],  # UVI 밴드만 사용
                        'min': -500, # 수중식물 지수의 최소값
                        'max': 500,   # 수중식물 지수의 최대값
                        # 'palette': ['purple', 'blue', 'green', 'yellow', 'red']  # 색상 팔레트 설정
                        'palette': ['#ffffb2','#fecc5c','#fd8d3c','#f03b20','#bd0026']  # 색상 팔레트 설정
                    }
                    
                    center = aoi.centroid().coordinates().getInfo()[::-1]
                    m3 = folium.Map(location=center, zoom_start=13)

                    # Add layers to the folium map.
                    try:
                        layer1 = make_layer(fai_s2_sr_first_img_parse,uvi_params,'S2 cloud-free mosaic')
                        layer2 = make_layer(fai_s2_sr_sec_img_parse,uvi_params,'S2 cloud-free mosaic')
                        sbs = folium.plugins.SideBySideLayers(layer1, layer2)

                        layer1.add_to(m3)
                        layer2.add_to(m3)
                        sbs.add_to(m3)
                        # Add a layer control panel to the map.
                        m3.add_child(folium.LayerControl())
                        plugins.Fullscreen().add_to(m3)
                        folium_static(m3, width = 650)
                    except:
                        st.write('해당일자에 해당하는 위성영상이 없습니다.')
                    
                with col6 :
                    try:
                        all_area = calculate_all_area(fai_s2_sr_first_img_parse,aoi)
                        area_1 = calculate_area(fai_s2_sr_first_img_parse,aoi,number)
                        area_2 = calculate_area(fai_s2_sr_sec_img_parse,aoi,number)
                        
                        df = pd.DataFrame({
                            "면적(km^2)": [all_area, area_1, area_2]
                        }, index=["관심영역 전체", "첫번째 사진", "두번째 사진"])

                        st.dataframe(df.T, use_container_width = True)
                        st.bar_chart(df.T, use_container_width = True)

                        st.write('FAI지수 통계')
                        st.dataframe(define_threshold(fai_s2_sr_sec_img_parse,aoi), use_container_width = True)
                    except:
                        st.write('면적이 너무 커서 계산을 할 수 없습니다.')

# launch
if __name__  == "__main__" :
    app()
    
