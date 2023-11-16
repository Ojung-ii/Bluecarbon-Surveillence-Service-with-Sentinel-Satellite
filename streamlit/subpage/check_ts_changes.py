import streamlit as st
import folium
from streamlit_folium import folium_static
from scipy.stats import norm, gamma, f, chi2
import json
import ee
from datetime import datetime, timedelta
import IPython.display as disp
import sar_func
# Google Earth Engine 초기화
ee.Initialize()

def app():
    # 페이지 설정과 제목
    vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179"
    layer = "Satellite"
    tileType = "jpeg"
    
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("⏱️ 시계열 변화탐지 확인")
        st.write("---"*20)

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
        start_date = st.date_input('시작날짜 선택하세요:')  
        end_date = st.date_input('끝날짜 선택하세요:')    

        # 분석 실행 버튼
        st.write("")
        proceed_button = st.button("☑️ 분석 실행")
        
        
    # 왼쪽 섹션: 폴리곤 매핑 시각화
    with col1:
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

    # 그래프 영역
    if proceed_button:
        def add_ee_layer(self, ee_image_object, vis_params, name):
                map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
                folium.raster_layers.TileLayer(
                    tiles = map_id_dict['tile_fetcher'].url_format,
                    attr = 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
                    name = name,
                    overlay = True,
                    control = True
            ).add_to(self)
        st.write("-----"*20)
        with st.spinner("변화탐지 분석중"):
            # 시간 앞 6일 뒤 5일 찾아보기
            # Add EE drawing method to folium.
            folium.Map.add_ee_layer = add_ee_layer
            aoi = sar_func.create_ee_polygon_from_geojson(aoi)
            
            start_f = start_date - timedelta(days=6)
            end_b = end_date + timedelta(days=5)
            start_f = start_f.strftime('%Y-%m-%d')
            end_b = end_b.strftime('%Y-%m-%d')
            # SAR load
            def to_ee_date(image):
                return ee.Date(image.get('date'))
            
            im_coll = (ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT')
                .filterBounds(aoi)
                .filterDate(ee.Date(start_f),ee.Date(end_b))
                .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
                # .filter(ee.Filter.eq('relativeOrbitNumber_start', 127))
                .map(lambda img: img.set('date', ee.Date(img.date()).format('YYYYMMdd')))
                .sort('date'))
            
            timestamplist = (im_coll.aggregate_array('date')
                        .map(lambda d: ee.String('T').cat(ee.String(d)))
                        .getInfo())
            #clip
            def clip_img(img):
                return ee.Image(img).clip(aoi)
            im_list = im_coll.toList(im_coll.size())
            im_list = ee.List(im_list.map(clip_img))

            #select vv
            def selectvv(current):
                return ee.Image(current).select('VV')

            vv_list = im_list.map(selectvv)
            location = aoi.centroid().coordinates().getInfo()[::-1]
            alpha = 0.01

            def omnibus(im_list, m4 = 4.4):
                def log(current):
                    return ee.Image(current).log()
                im_list = ee.List(im_list)
                k = im_list.length()
                klogk = k.multiply(k.log())
                klogk = ee.Image.constant(klogk)
                sumlogs = ee.ImageCollection(im_list.map(log)).reduce(ee.Reducer.sum())
                logsum = ee.ImageCollection(im_list).reduce(ee.Reducer.sum()).log()
                return klogk.add(sumlogs).subtract(logsum.multiply(k)).multiply(-2*m4)
            
            k = 26; alpha = 0.01

            # Run the algorithm with median filter and at 1% significance.
            result = ee.Dictionary(sar_func.change_maps(im_list, median=True, alpha=0.01))
            # Extract the change maps and export to assets.
            cmap = ee.Image(result.get('cmap'))
            smap = ee.Image(result.get('smap'))
            fmap = ee.Image(result.get('fmap'))
            bmap = ee.Image(result.get('bmap'))
            cmaps = ee.Image.cat(cmap, smap, fmap, bmap).rename(['cmap', 'smap', 'fmap']+timestamplist[1:])
            cmaps = cmaps.updateMask(cmaps.gt(0))
            location = aoi.centroid().coordinates().getInfo()[::-1]
            palette = ['black', 'red', 'cyan', 'yellow']

            # Define a method for displaying Earth Engine image tiles to folium map.
            mp = folium.Map(location=location, zoom_start=14,tiles=tiles, attr=attr)
            folium.TileLayer(
            tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
            attr='VWorld Hybrid',
            name='VWorld Hybrid',
            overlay=True
            ).add_to(mp)
            folium.LayerControl().add_to(m)
            #6달 이하는 전부 계산, 6달부터는 달마다, 1~3년까진 분기마다, 4년부턴 년마다의 변화
            perd = datetime.strptime(end_b, '%Y-%m-%d')-datetime.strptime(start_f   , '%Y-%m-%d')
            if perd<timedelta(180):
                for i in range(1,len(timestamplist)):
                    mp.add_ee_layer(cmaps.select(timestamplist[i]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i])
            elif perd < timedelta(365):
                for i in range(1,len(timestamplist),2):
                    mp.add_ee_layer(cmaps.select(timestamplist[i]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i])
            elif perd<timedelta(1095):
                for i in range(1,len(timestamplist),3):
                    mp.add_ee_layer(cmaps.select(timestamplist[i]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i])
            else:
                for i in range(1,len(timestamplist), 30):
                    mp.add_ee_layer(cmaps.select(timestamplist[i*30]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[i*30])
                mp.add_ee_layer(cmaps.select(timestamplist[-1]), {'min': 0,'max': 3, 'palette': palette}, timestamplist[-1])
            
            #folium에 추가
            mp.add_child(folium.LayerControl())
            
            # 스트림릿에 folium 지도 표시
            folium_static(mp)
            
# launch
if __name__  == "__main__" :
    app()
