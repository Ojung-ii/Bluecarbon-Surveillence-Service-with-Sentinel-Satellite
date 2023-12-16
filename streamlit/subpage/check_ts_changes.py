import streamlit as st 
import folium 
from folium import plugins
from streamlit_folium import folium_static 
from scipy.stats import norm, gamma, f, chi2
import json  
import ee  
from datetime import datetime, timedelta  
import IPython.display as disp 
import check_ts_changes_func 
import ts_trend_analysis_func
import time_func

# Google Earth Engine initialization
ee.Initialize()

# VWorld map settings
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
layer = "Satellite" 
tileType = "jpeg"  

# Define key application functions.
def app():
     # Page layout settings
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("⏱️ 시계열 변화탐지 확인")
        st.markdown("""
            <h3 style='text-align: left; font-size: 22px;'>( sentinel-1 : 레이더 위성영상 활용 )</h3>
            """, unsafe_allow_html=True)
        st.write("---"*20)
        if st.toggle("사용설명서"):
            st.write(
                '''
                시계열 변화탐지 기능 사용설명서
                    
                    1. 관심 영역 설정
                    2. 날짜 설정
                    3. 변화탐지 분석 실행
                    4. 결과 확인 및 해석
                        - 분석결과 우측상단의 레이어 선택 툴을 사용해 날짜별로 분석

                    * 주의사항 : 인터넷 연결 상태에 따라 분석 시간이 달라질 수 있습니다.
                     ''')

    # 'aoi.geojson' file load
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Importing a list of local names from a GeoJSON file.
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # Add a new option to the drop-down list.

    # Dividing sections
    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])

    # Area Of Interest initialization
    aoi = None

    # Input section
    with col2:
        with st.form("조건 폼"):

            # Select Area of Interest.
            selected_name = st.selectbox("관심 영역을 선택하세요:", area_names)
            
            # Enable file upload function when '새로운 관심영역 넣기' is selected.
            if selected_name == "새로운 관심영역 넣기":
                uploaded_file = st.file_uploader("GeoJSON 파일을 업로드하세요", type=['geojson'])
                if uploaded_file is not None:
                    aoi = json.load(uploaded_file)
            else:
                # Select an existing AOI.
                aoi = next((feature for feature in geojson_data['features'] if feature['properties']['name'] == selected_name), None)

            # Date Settings
            start_date = st.date_input('시작날짜 (2015.05 ~) :',time_func.one_month_ago_f_t()) # Default: Today - one month.
            end_date = st.date_input('끝날짜 선택하세요:')# Default: Today

            # Run Analysis button.
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")  
        
        
    # Visualization section
    with col1:
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        m = folium.Map(location=[36.5, 127.5], zoom_start=10,tiles=tiles, attr=attr)

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
        # Displaying a Map in a Streamlet.
        folium_static(m, width=600)

# ---------------------------- Result Screen ----------------------------
    # Page layout settings
    empty1, col3, empty2 = st.columns([0.12,0.8, 0.12])
    
   # Graph section
    if proceed_button:
        with col3:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  시계열 변화탐지 결과  ⬇️</h3>
            """, unsafe_allow_html=True)
            
            


            
            with st.spinner("변화탐지 분석중"):
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

                # HTML 
                html_content = """
                <div class="legend">
                <div class="legend-item">
                    <span class="color-box" style="background-color: red;"></span>
                    <span class="description">
                    <strong>반사율 증가:</strong><br>
                    식생 증가,<br>
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
                <div class="legend-item">
                    <span class="color-box" style="background-color: yellow;"></span>
                    <span class="description">
                    <strong>반사율 급변:</strong><br>
                    극적 지형/환경 변화
                    </span>
                </div>
                </div>
                """

                # Apply to Streamlit.
                st.markdown(css_style, unsafe_allow_html=True)
                st.markdown(html_content, unsafe_allow_html=True)
                st.write("")


                # Adding a Draw Plug-in to a Folium Map.
                folium.Map.add_ee_layer = check_ts_changes_func.add_ee_layer
                aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)
                
                # Calculate the date considering that the satellite(Sentinel-1) is a 12-day cycle.
                start_f = start_date - timedelta(days=6)
                end_b = end_date + timedelta(days=6)
                start_f = start_f.strftime('%Y-%m-%d')
                end_b = end_b.strftime('%Y-%m-%d')
                
                def to_ee_date(image):
                    return ee.Date(image.get('date'))
                
                # S1_GRD_FLOAT load
                im_coll = (ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT')
                    .filterBounds(aoi)
                    .filterDate(ee.Date(start_f),ee.Date(end_b))
                    .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
                    .map(lambda img: img.set('date', ee.Date(img.date()).format('YYYYMMdd')))
                    .sort('date'))
                
                # Create timestamplist.
                timestamplist = (im_coll.aggregate_array('date')
                            .map(lambda d: ee.String('T').cat(ee.String(d)))
                            .getInfo())
                
                # Define clip function.
                def clip_img(img):
                    return ee.Image(img).clip(aoi)
                im_list = im_coll.toList(im_coll.size())
                im_list = ee.List(im_list.map(clip_img))

                # VH band is rarely included. Select and output only VV band.
                def selectvv(current):
                    return ee.Image(current).select('VV')

                vv_list = im_list.map(selectvv)
                location = aoi.centroid().coordinates().getInfo()[::-1]

                # Run the algorithm with median filter and at 1% significance.
                result = ee.Dictionary(check_ts_changes_func.change_maps(im_list, median=True, alpha=0.01))
                # Extract the change maps and export to assets.
                cmap = ee.Image(result.get('cmap'))
                smap = ee.Image(result.get('smap'))
                fmap = ee.Image(result.get('fmap'))
                bmap = ee.Image(result.get('bmap'))
                cmaps = ee.Image.cat(cmap, smap, fmap, bmap).rename(['cmap', 'smap', 'fmap']+timestamplist[1:])
                cmaps = cmaps.updateMask(cmaps.gt(0))
                location = aoi.centroid().coordinates().getInfo()[::-1]
                palette = ['black', 'red', 'blue', 'yellow']

                mp = folium.Map(location=location, zoom_start=14,tiles=tiles, attr=attr)
                folium.TileLayer(
                tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
                attr='VWorld Hybrid',
                name='VWorld Hybrid',
                overlay=True
                ).add_to(mp)

                # Add C_map layer.
                for i in range(1,len(timestamplist)):
                    mp.add_ee_layer(cmaps.select(timestamplist[i]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i])

                mp.add_child(folium.LayerControl())
                # Displaying a Map in a Streamlet.
                plugins.Fullscreen().add_to(mp)
                folium_static(mp,width=970)


# launch
if __name__  == "__main__" :
    app()
