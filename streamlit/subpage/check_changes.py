import streamlit as st
import folium
from streamlit_folium import folium_static 
from scipy.stats import norm, gamma, f, chi2
import json 
import ee  
from datetime import datetime, timedelta 
import IPython.display as disp 
import check_ts_changes_func # 변화탐지 관련 함수 모듈
from scipy.optimize import bisect 
import ts_trend_analysis_func
import time_func
# Google Earth Engine 초기화
ee.Initialize()

# VWorld 지도 설정
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API 키
layer = "Satellite" # VWorld 레이어
tileType = "jpeg" # 타일 유형

# 주요 애플리케이션 함수 정의
def app():
    k=0
    # 페이지 레이아웃 설정
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("🔍 변화탐지 확인") # 페이지 제목
        st.write("---"*20) # 구분선
        if st.toggle("사용설명서"):
            st.write("""
이 사용설명서는 Sentinel-1 위성 데이터를 활용하여 지정된 지역에서 변화탐지를 수행하는 Streamlit 웹입니다.

1. 웹 애플리케이션 접속
Streamlit 웹 애플리케이션의 URL을 웹 브라우저에 입력하여 접속합니다.
2. 관심 지역 및 날짜 설정
화면에서 '관심 지역을 선택하세요:' 드롭다운 메뉴를 통해 분석할 지역을 선택합니다. 이미 정의된 지역을 선택하거나, '새로운 관심영역 넣기' 옵션으로 GeoJSON 파일을 업로드하여 새로운 지역을 추가할 수 있습니다.
'시작날짜 선택하세요:' 및 '끝날짜 선택하세요:' 옵션을 사용하여 분석할 기간을 설정합니다.
3. 변화탐지 분석 실행
'분석 실행' 버튼을 클릭하여 변화탐지 분석을 시작합니다.
4. 결과 확인 및 해석
변화탐지 분석이 완료되면, 지정된 지역에 대한 시계열 변화탐지 결과가 지도 위에 표시됩니다.
지도에는 다음과 같은 색상으로 변화가 표시됩니다:
빨간색: 반사율 증가 (구조물 또는 식생 증가, 물 면적 감소)
파란색: 반사율 감소 (구조물 또는 식생 감소, 물 면적 증가)
노란색: 반사율 급변 (극적 지형/환경 변화)
5. 추가 기능
지도에 추가된 레이어 컨트롤을 통해 다양한 시각에서 지역을 관찰할 수 있습니다.
지도의 VWorld Satellite 및 Hybrid 레이어 옵션을 통해 지역의 다른 모습을 볼 수 있습니다.
주의사항
인터넷 연결 상태에 따라 분석 시간이 달라질 수 있습니다.
모든 데이터와 분석 결과는 Google Earth Engine을 통해 제공되는 최신 위성 이미지에 기반합니다.
GeoJSON 파일은 정확한 지리적 경계를 나타내야 하며, 파일 형식이 올바르지 않을 경우 분석이 제대로 수행되지 않을 수 있습니다.
이 사용설명서를 따라 변화탐지 확인 툴을 사용하면, Sentinel-1 위성 데이터를 활용하여 지정된 기간과 지역에 대한 시계열 변화를 손쉽게 탐지하고 분석할 수 있습니다.
                     """)

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as ff:
        geojson_data = json.load(ff)

    # GeoJSON 파일에서 지역 이름 목록 가져오기
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
            start_date = st.date_input('시작날짜 선택하세요:',time_func.one_month_ago_f())
            end_date = st.date_input('끝날짜 선택하세요:')    

            # 분석 실행 버튼
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")
        
       
    # 왼쪽 섹션: 폴리곤 매핑 시각화
    with col1:
        # 지도 초기화 (대한민국 중심 위치로 설정)
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        m = folium.Map(location=[36.5, 127.5], zoom_start=7,tiles=tiles, attr = attr)

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
        folium_static(m, width=600)

# ---------------------------- 결과  ---------------------------
    # 페이지 레이아웃 설정
    empty1, col3, empty2 = st.columns([0.12,0.8, 0.12])

    # 그래프 영역
    if proceed_button:
        k=0
        with col3:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  변화탐지 결과  ⬇️</h3>
            """, unsafe_allow_html=True)
            st.write('')
            st.write('')
            with st.spinner("변화탐지 분석중"):
                

                # Folium에 Earth Engine 그리기 메서드 추가
                folium.Map.add_ee_layer = check_ts_changes_func.add_ee_layer
                # GeoJSON 파일에서 추출한 관심 지역을 Earth Engine 폴리곤으로 변환
                aoi = ts_trend_analysis_func.create_ee_polygon_from_geojson(aoi)

                #위성이 12일 주기인 것을 고려하여 선택된 날짜 앞뒤 6일에 영상이 있는지 확인하기 위해 날짜 더하고 빼주는 코드
                start_f = start_date - timedelta(days=6)
                start_b = start_date + timedelta(days=5)
                end_f = end_date - timedelta(days=6)
                end_b = end_date + timedelta(days=5)
                start_f = start_f.strftime('%Y-%m-%d')
                end_f = end_f.strftime('%Y-%m-%d')
                start_b = start_b.strftime('%Y-%m-%d')
                end_b = end_b.strftime('%Y-%m-%d')
            
                # SAR 데이터(Float) 로드
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

                #VH는 거의 없어 VV만으로
                im1 = ee.Image(ffa_fl).select('VV').clip(aoi)
                im2 = ee.Image(ffb_fl).select('VV').clip(aoi)
                
                ratio = im1.divide(im2)
            
                # 두장의 비율 이미지 Ratio에 대한 통계값 계산
                # 히스토그램/평균/분산(최소,최대)
                try:
                    hist = ratio.reduceRegion(ee.Reducer.fixedHistogram(0, 5, 500), aoi).get('VV').getInfo()
                except Exception as e:
                    st.write("시작날짜 혹은 끝날짜에 해당되는 SAR위성영상이 없습니다.")
                    k=1
                if k==0:
                    mean = ratio.reduceRegion(ee.Reducer.mean(), aoi).get('VV').getInfo()
                    variance = ratio.reduceRegion(ee.Reducer.variance(), aoi).get('VV').getInfo()
                    v_min = ratio.select('VV').reduceRegion(
                        ee.Reducer.min(), aoi).get('VV').getInfo()
                    v_max = ratio.select('VV').reduceRegion(
                        ee.Reducer.max(), aoi).get('VV').getInfo()

                    m1 = 5 # 임의의 값
                    # F-분포의 CDF 함수를 정의
                    dt = f.ppf(0.0005, 2*m1, 2*m1)

                    # LRT(Likelihood Ratio Test:우도비 검정) 통계량 계산
                    q1 = im1.divide(im2)
                    q2 = im2.divide(im1)

                    # Change map: 0 = 변화 없음, 1 = 강도 감소, 2 = 강도 증가
                    c_map = im1.multiply(0).where(q2.lt(dt), 1)#먼저 0으로 다 곱하고 감소면 1
                    c_map = c_map.where(q1.lt(dt), 2)#증가면 2

                    # 변화 없는(no change) 픽셀 마스크 처리
                    c_map = c_map.updateMask(c_map.gt(0))

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

                    # 변화 지도 레이어 추가 
                    mp.add_ee_layer(c_map,
                                    {'min': 0, 'max': 2, 'palette': ['00000000', '#FF000080', '#0000FF80']},  # 변화 없음: 투명, 감소: 반투명 파랑, 증가: 반투명 빨강
                                    'Change Map')
                    mp.add_child(folium.LayerControl())

                    # 스트림릿에 folium맵 출력
                    folium_static(mp,width=970)

                # ---------------------- 범례 ---------------------- 
                st.write("")    
                # CSS 스타일
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

                # HTML 내용
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

                # Streamlit에 적용
                st.markdown(css_style, unsafe_allow_html=True)
                st.markdown(html_content, unsafe_allow_html=True)
           
       
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
                    # Extract and display the date of image
                    im1_date = ee.Image(ffa_fl).date().format('YYYY-MM-dd').getInfo()
                    im2_date = ee.Image(ffb_fl).date().format('YYYY-MM-dd').getInfo()
                    with col4:
                        st.write(f"Before : {im1_date}")
                    with col5 : 
                        st.write(f"After : {im2_date}")


                    #계산없이 이미지로 바로 볼 때는 GRD 불러오는 게 좋음
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
                    
                    # VV 뽑기
                    ffa_fl = ee.Image(ffa_fl).select('VV').clip(aoi)
                    ffb_fl =ee.Image(ffb_fl).select('VV').clip(aoi)

                    #영상 tile로 만들기
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
                    # 시각화 매개변수
                    vis_params = {'min': -20, 'max': 0}

                    # 레이어 맹글기
                    ffa_fl_layer = make_layer(ffa_fl, vis_params, 'Image 1')
                    ffb_fl_layer = make_layer(ffb_fl, vis_params, 'Image 2')

                    # Side by Side 플러그인 사용을 위해 만든 레이어 sbs에 넣고 mp2에 추가
                    sbs = folium.plugins.SideBySideLayers(ffa_fl_layer, ffb_fl_layer)
                    ffa_fl_layer.add_to(mp2)
                    ffb_fl_layer.add_to(mp2)
                    sbs.add_to(mp2)

                    # 스트림릿에 folium맵 출력
                    folium_static(mp2,width=970)


# launch
if __name__  == "__main__" :
    app()