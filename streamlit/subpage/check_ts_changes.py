import streamlit as st 
import folium 
from streamlit_folium import folium_static 
from scipy.stats import norm, gamma, f, chi2
import json  
import ee  
from datetime import datetime, timedelta  
import IPython.display as disp 
import check_ts_changes_func 

# Google Earth Engine 초기화
ee.Initialize()

# VWorld 지도 설정
vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
layer = "Satellite" 
tileType = "jpeg"  

# 주요 애플리케이션 함수 정의
def app():
    # 페이지 레이아웃 설정
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("⏱️ 시계열 변화탐지 확인") # 페이지 제목
        st.write("---"*20) # 구분선

    # 'aoi.geojson' 파일 로드
    with open('aoi.geojson', 'r', encoding="utf-8") as f:
        geojson_data = json.load(f)

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
            start_date = st.date_input('시작날짜 선택하세요:') # 디폴트: 오늘 날짜
            end_date = st.date_input('끝날짜 선택하세요:') # 디폴트: 오늘 날짜

            # 분석 실행 버튼
            st.write("")
            proceed_button = st.form_submit_button("☑️ 분석 실행")  
        
        
    # 왼쪽 섹션: 폴리곤 매핑 시각화
    with col1:
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        m = folium.Map(location=[36.5, 127.5], zoom_start=10,tiles=tiles, attr=attr)

        # 선택된 관심 지역이 있을 경우에 해당 지역 폴리곤 표시
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

# ---------------------------- 결과  ---------------------------
    # 섹션 나누기
    empty1, col3, empty2 = st.columns([0.12,0.8, 0.12])
    
    # 페이지 레이아웃 설정
    if proceed_button:
        with col3:
            st.write("-----"*20)
            st.markdown("""
            <h3 style='text-align: center; font-size: 35px;'>⬇️  시계열 변화탐지 결과  ⬇️</h3>
            """, unsafe_allow_html=True)
            
            # 섹션 나누기
            col4, col5  = st.columns([0.8,0.08])

            # 왼쪽 섹션: 변화탐지 분석
            with col4 : 
            
                with st.spinner("변화탐지 분석중"):
                    st.write('')
                    st.write('')

                    # Earth Engine에서 Folium 지도에 레이어 추가하는 메서드


                    # Folium에 Earth Engine 그리기 메서드 추가
                    folium.Map.add_ee_layer = check_ts_changes_func.add_ee_layer
                    aoi = check_ts_changes_func.create_ee_polygon_from_geojson(aoi)
                    
                    #위성이 12일 주기인 것을 고려하여 선택된 날짜 앞뒤 6일에 영상이 있는지 확인하기 위해 날짜 더하고 빼주는 코드
                    start_f = start_date - timedelta(days=6)
                    end_b = end_date + timedelta(days=6)
                    start_f = start_f.strftime('%Y-%m-%d')
                    end_b = end_b.strftime('%Y-%m-%d')
                   
                    def to_ee_date(image):
                        return ee.Date(image.get('date'))
                    
                    # Earth Engine에서 SAR 데이터 로드
                    im_coll = (ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT')
                        .filterBounds(aoi)
                        .filterDate(ee.Date(start_f),ee.Date(end_b))
                        .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
                        .map(lambda img: img.set('date', ee.Date(img.date()).format('YYYYMMdd')))
                        .sort('date'))
                    
                    # 시간 스탬프 리스트 생성
                    timestamplist = (im_coll.aggregate_array('date')
                                .map(lambda d: ee.String('T').cat(ee.String(d)))
                                .getInfo())
                    
                    # 원하는 지역 clip
                    def clip_img(img):
                        return ee.Image(img).clip(aoi)
                    im_list = im_coll.toList(im_coll.size())
                    im_list = ee.List(im_list.map(clip_img))

                    # VV 밴드 선택
                    def selectvv(current):
                        return ee.Image(current).select('VV')

                    vv_list = im_list.map(selectvv)
                    location = aoi.centroid().coordinates().getInfo()[::-1]
                    alpha = 0.01
                    
                    k = 26; alpha = 0.01

                    # 중간값 필터 및 1% 유의수준으로 알고리즘 실행
                    result = ee.Dictionary(check_ts_changes_func.change_maps(im_list, median=True, alpha=0.01))
                    cmap = ee.Image(result.get('cmap'))
                    smap = ee.Image(result.get('smap'))
                    fmap = ee.Image(result.get('fmap'))
                    bmap = ee.Image(result.get('bmap'))
                    cmaps = ee.Image.cat(cmap, smap, fmap, bmap).rename(['cmap', 'smap', 'fmap']+timestamplist[1:])
                    cmaps = cmaps.updateMask(cmaps.gt(0))
                    location = aoi.centroid().coordinates().getInfo()[::-1]
                    palette = ['black', 'red', 'blue', 'yellow']

                    
                    # Folium 지도 생성
                    mp = folium.Map(location=location, zoom_start=14,tiles=tiles, attr=attr)
                    folium.TileLayer(
                    tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
                    attr='VWorld Hybrid',
                    name='VWorld Hybrid',
                    overlay=True
                    ).add_to(mp)

                    # 시점별 변화 지도 맵 레이어에 추가
                    for i in range(1,len(timestamplist)):
                        mp.add_ee_layer(cmaps.select(timestamplist[i]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i])
                    
                    # folium에 추가
                    mp.add_child(folium.LayerControl())
                    
                    # 스트림릿에 folium 지도 출력
                    folium_static(mp,width=870)
            
            # 범례 및 설명 추가
            with col5:
                st.write("")
                st.write("")
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
                                    .yellow { background-color: yellow; }
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
                                    <div class="legend-item">
                                        <div class="color-box yellow"></div>
                                        <span>이상</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                
                
# launch
if __name__  == "__main__" :
    app()
