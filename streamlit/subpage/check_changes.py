import streamlit as st
import folium
from streamlit_folium import folium_static 
from scipy.stats import norm, gamma, f, chi2
import json 
import ee  
from datetime import datetime, timedelta 
import IPython.display as disp 
import check_ts_changes_func 
from scipy.optimize import bisect 
import ts_trend_analysis_func
import time_func
from folium import plugins
# Google Earth Engine Initialization
ee.Initialize()

# VWorld map settings
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API key
layer = "Satellite" # VWorld layer
tileType = "jpeg" # Tile type

# Define key application functions.
def app():
    
    # File download function
    def get_download_url(image, vis_params, region):
        download_url = image.getDownloadURL({
            'scale': 30,  # 해상도 설정
            'crs': 'EPSG:4326',
            'region': region.getInfo() if isinstance(region, ee.Geometry) else region,
            **vis_params
        })
        return download_url
    
    k=0
    # Page layout settings
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("🔍 변화탐지 확인") 
        st.markdown("""
            <h3 style='text-align: left; font-size: 22px;'>( sentinel-1 : 레이더 위성영상 활용 )</h3>
            """, unsafe_allow_html=True)
        st.write("---"*20) # A dividing line
        if st.toggle("사용설명서"):
            st.write("""
                변화탐지 기능 사용설명서
                    
                    - 맹꽁이 서식지와 같은 습지와 침수지역 등의 변화를 확인하는데 유용합니다.
                    
                    1. 관심 영역 설정
                    2. 날짜 설정
                    3. 변화탐지 분석 실행
                    4. 결과 확인 및 해석
                    5. 변화 전과 후 비교 (슬라이더)
                    
                    * 주의사항 : 인터넷 연결 상태에 따라 분석 시간이 달라질 수 있습니다.
                     """)

    # 'aoi.geojson' file load
    with open('aoi.geojson', 'r', encoding="utf-8") as ff:
        geojson_data = json.load(ff)

    # Importing a list of local names from a GeoJSON file.
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # Add a new option to the drop-down list.

    # Dividing sections.
    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])

    # Area Of Interest initialization
    aoi = None

    # Input section
    with col2:
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

            # Date Settings
            start_date = st.date_input('시작날짜 (2015.05 ~) :',time_func.one_month_ago_f_t()) # Default: Today - one month
            end_date = st.date_input('끝날짜 (~ 오늘) :') # Default: Today

            # Run Analysis button.
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")
            
       
    # Visualization section
    with col1:
        # Map initialization (set as Korea's central location)
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        m = folium.Map(location=[36.5, 127.5], zoom_start=7,tiles=tiles, attr = attr)

        # Display the local polygon only if there is a selected AOI.
        if aoi:
            folium.GeoJson(
                aoi,
                name=selected_name,
                style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}
            ).add_to(m)
            
            # Adjust the map to fit the selected polygon.
            m.fit_bounds(folium.GeoJson(aoi).get_bounds())
        folium.TileLayer(
            tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
            attr='VWorld Hybrid',
            name='VWorld Hybrid',
            overlay=True
        ).add_to(m)
        folium.LayerControl().add_to(m)
        plugins.Fullscreen().add_to(m)
        folium_static(m, width=600)

# ---------------------------- Result Screen ---------------------------
    # Page layout settings
    empty1, col3, empty2 = st.columns([0.12,0.8, 0.12])

    # Graph section
    if proceed_button : 
        k=0
        with col3:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  변화탐지 결과  ⬇️</h3>
            """, unsafe_allow_html=True)
            st.write("")    

            
            with st.spinner("변화탐지 분석중"):
                
                # Adding a Draw Plug-in to a Folium Map.
                folium.Map.add_ee_layer = check_ts_changes_func.add_ee_layer
                # Convert AOI extracted from GeoJSON file to Earth Engine polygon.
                aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)

                # Calculate the date considering that the satellite(Sentinel-1) is a 12-day cycle.
                start_f = start_date - timedelta(days=6)
                start_b = start_date + timedelta(days=5)
                end_f = end_date - timedelta(days=6)
                end_b = end_date + timedelta(days=5)
                start_f = start_f.strftime('%Y-%m-%d')
                end_f = end_f.strftime('%Y-%m-%d')
                start_b = start_b.strftime('%Y-%m-%d')
                end_b = end_b.strftime('%Y-%m-%d')
            
                # S1_GRD_FLOAT load
                ffa_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') 
                                    .filterBounds(aoi) 
                                    .filterDate(ee.Date(start_f), ee.Date(start_b))
                                    .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
                                    .first() 
                                    .clip(aoi))
                ffb_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') 
                                    .filterBounds(aoi) 
                                    .filterDate(ee.Date(end_f), ee.Date(end_b))
                                    .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING')) 
                                    .first() 
                                    .clip(aoi))

                # VH band is rarely included. Select and output only VV band.
                im1 = ee.Image(ffa_fl).select('VV').clip(aoi)
                im2 = ee.Image(ffb_fl).select('VV').clip(aoi)
                
                ratio = im1.divide(im2)
            
                # Calculate statistics for two proportional image ratios.
                try:
                    hist = ratio.reduceRegion(ee.Reducer.fixedHistogram(0, 5, 500), aoi).get('VV').getInfo()
                except Exception as e:
                    st.write("시작날짜 혹은 끝날짜에 해당되는 SAR위성영상이 없습니다.")
                    k=1
                    
                if k==0: # If no exceptions have occurred, do the code below.
                    m1 = 5 # degree of freedom
                    # Calculate F distribution PPF(Percentile Point Function).
                    dt = f.ppf(0.0005, 2*m1, 2*m1)

                    # LRT(Likelihood Ratio Test) statistics
                    q1 = im1.divide(im2)
                    q2 = im2.divide(im1)

                    # Change map with 0 = no change, 1 = decrease, 2 = increase in intensity.
                    c_map = im1.multiply(0).where(q2.lt(dt), 1) #Change all values to zero first and the reduced parts to one.
                    c_map = c_map.where(q1.lt(dt), 2)#The increasing parts to two.

                    # Mask no-change pixels.
                    c_map = c_map.updateMask(c_map.gt(0))
                                                   
                    
                    # Display map with red for increase and blue for decrease in intensity.
                    location = aoi.centroid().coordinates().getInfo()[::-1]
                    mp = folium.Map(
                        location=location,
                        zoom_start=14, tiles= tiles, attr = attr)
                    folium.TileLayer(
                        tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
                        attr='VWorld Hybrid',
                        name='VWorld Hybrid',
                        overlay=True
                    ).add_to(mp)
                    folium.LayerControl().add_to(m)

                    # Add C_map layer.
                    mp.add_ee_layer(c_map,
                                    {'min': 0, 'max': 2, 'palette': ['black', 'blue', 'red']},  
                                    'Change Map')
                    mp.add_child(folium.LayerControl())

                    # Displaying a Map in a Streamlet.
                    folium_static(mp,width=970)


                # ---------------------- Legend ---------------------- 
                st.write("")    
                # CSS style
                css_style = """
                <style>
                .legend {
                border: 1px solid #ddd;
                padding: 10px;
                background-color: #f9f9f9;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: space-evenly;
                }

                .legend-item {
                display: flex;
                align-items: center;
                }

                .color-box {
                width: 30px;
                height: 30px;
                margin-right: 10px;
                border: 1px solid #000;
                }

                .description {
                font-size: 15px;
                }
                </style>
                """

                # HTML content
                html_content = """
                <div class="legend">
                <div class="legend-item">
                    <span class="color-box" style="background-color: red;"></span>
                    <span class="description">
                    <strong>반사율 증가:</strong><br>
                    구조물 또는 식생 증가,<br>
                    물 면적 감소
                    </span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background-color: blue;"></span>
                    <span class="description">
                    <strong>반사율 감소:</strong><br>
                    구조물 또는 식생 감소, <br>
                    물 면적 증가
                    </span>
                </div>
                """

                # Apply to Streamlit.
                st.markdown(css_style, unsafe_allow_html=True)
                st.markdown(html_content, unsafe_allow_html=True)
                        
                    
               # --------------- calculated area values --------------------------------
               
                total_area = ee.Image.pixelArea().clip(aoi).reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=aoi,
                        scale=10  # Sentinel-1의 해상도
                ).getInfo()['area']

                decreased_area = c_map.eq(1).multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=aoi,
                    scale=10  # Sentinel-1의 해상도
                ).getInfo()['VV']

                # 증가한 영역(빨간색)의 면적 계산
                increased_area = c_map.eq(2).multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=aoi,
                    scale=10  # Sentinel-1의 해상도
                ).getInfo()['VV']


                st.write(f"전체 면적: {round(total_area,1)}m^2")
                st.write(f"파란색(감소) 영역 면적: {round(decreased_area,1)}m^2")
                st.write(f"빨간색(증가) 영역 면적: {round(increased_area,1)}m^2")
       
                # ------------- side by side map -------------------------
                if k==0:
                    # before&after title
                    st.write("-----"*20)
                    st.markdown("""
                    <h3 style='text-align: center; font-size: 25px;'>⬇️  Before & After  ⬇️</h3>
                    """, unsafe_allow_html=True)
                    st.write('')
                    st.write('')
                    
                    col4, col5 = st.columns([0.5,0.5])
                    # Extract and display the date of image.
                    im1_date = ee.Image(ffa_fl).date().format('YYYY-MM-dd').getInfo()
                    im2_date = ee.Image(ffb_fl).date().format('YYYY-MM-dd').getInfo()
                    with col4:
                        st.write(f"Before : {im1_date}")
                    with col5 : 
                        st.write(f"After : {im2_date}")


                    #It is better to import GRD when viewed directly in an image without calculation.
                    ffa_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                                            .filterBounds(aoi) 
                                            .filterDate(ee.Date(start_f), ee.Date(start_b))
                                            .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
                                            .first())
                                            
                                            
                    ffb_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                                            .filterBounds(aoi) 
                                            .filterDate(ee.Date(end_f), ee.Date(end_b))
                                            .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING')) 
                                            .first()) 
                    
                    # Extract VV.
                    ffa_fl = ee.Image(ffa_fl).select('VV').clip(aoi)
                    ffb_fl =ee.Image(ffb_fl).select('VV').clip(aoi)

                    # To create a side by side map, the value of control must be False.
                    def make_layer(ee_image_object, vis_params, name):
                        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
                        tile_layer = folium.raster_layers.TileLayer(
                            tiles=map_id_dict['tile_fetcher'].url_format,
                            attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
                            name=name,
                            overlay=True,
                            control=False
                        )
                        return tile_layer
                    
                    mp2 = folium.Map(location=location, zoom_start=14, tiles= tiles, attr = attr)
                    folium.TileLayer(
                        tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
                        attr='VWorld Hybrid',
                        name='VWorld Hybrid',
                        overlay=True
                    ).add_to(mp)
                    folium.LayerControl().add_to(m)

                    vis_params = {'min': -20, 'max': 0}

                    # Create a layer to side into the map.
                    ffa_fl_layer = make_layer(ffa_fl, vis_params, 'Image 1')
                    ffb_fl_layer = make_layer(ffb_fl, vis_params, 'Image 2')

                    # Add layer made for side by side plug-in to sbs and add sbs to mp2.
                    sbs = folium.plugins.SideBySideLayers(ffa_fl_layer, ffb_fl_layer)
                    ffa_fl_layer.add_to(mp2)
                    ffb_fl_layer.add_to(mp2)
                    sbs.add_to(mp2)
                    plugins.Fullscreen().add_to(mp2)
                    # Displaying a Map in a Streamlet.
                    folium_static(mp2,width=970)


# launch
if __name__  == "__main__" :
    app()