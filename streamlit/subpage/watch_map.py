import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from io import BytesIO
import json
import os

# Define key application functions.
def app():
    # Page layout settings
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("🗺️ 지도확인")
        st.write("---" * 20)

        # VWorld map settings
        vworld_key="3F753587-6509-3D99-8F79-9B82473EAAAF" # VWorld API key
        layer = "Satellite" # VWorld layer
        tileType = "jpeg" # Tile type

        # Setting up the path to the ROI file.
        geojson_path = 'aoi.geojson'

        # Import or initialize region of interest data.
        if os.path.exists(geojson_path):
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        else:
            geojson_data = {"type": "FeatureCollection", "features": []}

        # Extract the list of interest names.
        aoi_names = [feature["properties"]["name"] for feature in geojson_data["features"]]


        st.subheader("AOI 조회 및 시각화")
        tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
        attr = "Vworld"
        
        m = folium.Map(location=[36.6384, 127.6961], zoom_start=7,tiles=tiles, attr=attr)
        folium.TileLayer(
        tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
        attr='VWorld Hybrid',
        name='VWorld Hybrid',
        overlay=True
        ).add_to(m)
        selected_aoi_name = st.selectbox('관심 영역을 선택하세요:', aoi_names)
        selected_aoi = next((feature for feature in geojson_data["features"]
                            if feature["properties"]["name"] == selected_aoi_name), None)
        
        if st.button('관심 영역 조회'):
        # Display the local polygon only if there is a selected AOI.
            if selected_aoi:
                folium.GeoJson(
                    selected_aoi,
                    name=selected_aoi_name,
                    style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}
                ).add_to(m)
                # Adjust the map to fit the selected polygon.
                m.fit_bounds(folium.GeoJson(selected_aoi).get_bounds())

            else:
                st.error("선택된 관심 영역을 찾을 수 없습니다.")
        # Displaying a Map in a Streamlet.
        folium_static(m)



# launch
if __name__  == "__main__" :
    app()
    
    