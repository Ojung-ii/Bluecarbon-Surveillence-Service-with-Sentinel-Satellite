
import streamlit as st
import folium
from streamlit_folium import folium_static
from scipy.stats import norm, gamma, f, chi2
import json
import ee
from datetime import datetime, timedelta
import IPython.display as disp
import sar_func
from scipy.optimize import bisect

# Google Earth Engine 초기화
ee.Initialize()

# 페이지 설정과 제목
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
layer = "Satellite"
tileType = "jpeg"

def app():
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("🔍 변화탐지 확인")
        st.write("---"*20)

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as ff:
        geojson_data = json.load(ff)

    # 관심 지역 목록
    area_names = [feature['properties']['name'] for feature in geojson_data['features']]
    area_names.append("새로운 관심영역 넣기")  # 드롭다운 목록에 새 옵션 추가

    # 섹션 나누기
    empty1, col1, col2, empty2 = st.columns([0.1,0.5, 0.3, 0.1])

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
        start_date = st.date_input('시작날짜 선택하세요:')  # 디폴트로 오늘 날짜가 찍혀 있다.
        end_date = st.date_input('끝날짜 선택하세요:')    # 디폴트로 오늘 날짜가 찍혀 있다.

        # 분석 실행 버튼
        st.write("")
        proceed_button = st.button("☑️ 분석 실행")
        
       
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

    empty1, col3, empty2 = st.columns([0.12,0.8, 0.12])
    # 그래프 영역
    if proceed_button:
        with col3:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  변화탐지 결과  ⬇️</h3>
            """, unsafe_allow_html=True)

            col4, col5 = st.columns([0.8,0.08])
            
            with col4 : 
                with st.spinner("변화탐지 분석중"):
                    st.write('')
                    st.write('')
                    def add_ee_layer(self, ee_image_object, vis_params, name):
                            map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
                            folium.raster_layers.TileLayer(
                                tiles = map_id_dict['tile_fetcher'].url_format,
                                attr = 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
                                name = name,
                                overlay = True,
                                control = True
                        ).add_to(self)

                        # Add EE drawing method to folium.
                    folium.Map.add_ee_layer = add_ee_layer
                    aoi = sar_func.create_ee_polygon_from_geojson(aoi)
                    # 시간 앞 6일 뒤 5일 찾아보기
                    start_f = start_date - timedelta(days=6)
                    start_b = start_date + timedelta(days=5)
                    end_f = end_date - timedelta(days=6)
                    end_b = end_date + timedelta(days=5)
                    start_f = start_f.strftime('%Y-%m-%d')
                    end_f = end_f.strftime('%Y-%m-%d')
                    start_b = start_b.strftime('%Y-%m-%d')
                    end_b = end_b.strftime('%Y-%m-%d')
                
                    # SAR load
                    ffa_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') 
                                        .filterBounds(aoi) 
                                        .filterDate(ee.Date(start_f), ee.Date(start_b)) 
                                        .first() 
                                        .clip(aoi))
                    ffb_fl = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') 
                                        .filterBounds(aoi) 
                                        .filterDate(ee.Date(end_f), ee.Date(end_b)) 
                                        .first() 
                                        .clip(aoi))
                    im1 = ee.Image(ffa_fl).select('VV').clip(aoi)
                    im2 = ee.Image(ffb_fl).select('VV').clip(aoi)
                    ratio = im1.divide(im2)

                    # ffa_fa에 대한 min, max 같은 통계값
                    hist = ratio.reduceRegion(ee.Reducer.fixedHistogram(0, 5, 500), aoi).get('VV').getInfo()
                    mean = ratio.reduceRegion(ee.Reducer.mean(), aoi).get('VV').getInfo()
                    variance = ratio.reduceRegion(ee.Reducer.variance(), aoi).get('VV').getInfo()
                    v_min = ratio.select('VV').reduceRegion(
                        ee.Reducer.min(), aoi).get('VV').getInfo()
                    v_max = ratio.select('VV').reduceRegion(
                        ee.Reducer.max(), aoi).get('VV').getInfo()

                    m1 = 5 # 걍 해둠ㅋㅋ
                    # F-분포의 CDF 함수를 정의합니다.
                    dt = f.ppf(0.0005, 2*m1, 2*m1)

                    # LRT statistics.
                    q1 = im1.divide(im2)
                    q2 = im2.divide(im1)

                    # Change map with 0 = no change, 1 = decrease, 2 = increase in intensity.
                    c_map = im1.multiply(0).where(q2.lt(dt), 1)
                    c_map = c_map.where(q1.lt(dt), 2)

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
                    # mp.add_ee_layer(ratio,
                    #                 {'min': v_min, 'max': v_max, 'palette': ['black', 'white']}, 'Ratio')
                    mp.add_ee_layer(c_map,
                                    {'min': 0, 'max': 2, 'palette': ['00000000', '#FF000080', '#0000FF80']},  # 변화 없음: 투명, 감소: 반투명 파랑, 증가: 반투명 빨강
                                    'Change Map')
                    mp.add_child(folium.LayerControl())

                    folium_static(mp,width=870)

            with col5:
                st.write('')
                st.write('')
                st.markdown("""
                                <style>
                                    .legend {
                                        border: 1px solid #ccc;
                                        padding: 10px;
                                        margin-top: 20px;
                                    }
                                    .legend-item {
                                        display: flex;
                                        align-items: center;
                                        margin-bottom: 5px;
                                    }
                                    .color-box {
                                        width: 20px;
                                        height: 20px;
                                        margin-right: 10px;
                                    }
                                    .red { background-color: red; }
                                    .blue { background-color: blue; }
                                </style>
                                <div class="legend">
                                    <div class="legend-item">
                                        <div class="color-box red"></div>
                                        <span>상승</span>
                                    </div>
                                    <div class="legend-item">
                                        <div class="color-box blue"></div>
                                        <span>하락</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
            
            col6, empty3 = st.columns([0.8, 0.12])
            with col6:
                # Extract and display the date of the first image
                im1_date = ee.Image(ffa_fl).first().date().format('YYYY-MM-dd').getInfo()
                im2_date = ee.Image(ffb_fl).first().date().format('YYYY-MM-dd').getInfo()
                st.write(f"사용된 첫 번째 사진의 날짜: {im1_date}")
                # Extract and display the date of the second image
                st.write(f"사용된 두 번째 사진의 날짜: {im2_date}")


# launch
if __name__  == "__main__" :
    app()