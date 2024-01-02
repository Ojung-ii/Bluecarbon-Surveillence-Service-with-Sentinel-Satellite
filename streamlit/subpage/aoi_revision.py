import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from io import BytesIO
import json
import os

def app():
    # Page layout settings.
    empty1, col0, empty2 = st.columns([0.1,1.0, 0.1])
    with col0:
        st.title("📍 관심영역 업데이트") 
        st.write("---" * 20)

        # Set up VWorld Map. 
        vworld_key="74C1313D-E1E1-3B8D-BCB8-000EEB21C179" # VWorld API key
        layer = "Satellite" # VWorld layer
        tileType = "jpeg" # tile type

        # Set up the path to the region of interest file.
        geojson_path = 'streamlit/aoi.geojson'

        # Importing or initializing region of interest data.
        if os.path.exists(geojson_path):
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        else:
            geojson_data = {"type": "FeatureCollection", "features": []}

        # Extract the list of interest names.
        aoi_names = [feature["properties"]["name"] for feature in geojson_data["features"]]

        # Create a tab.
        tab1, tab2, tab3 = st.tabs(["조회", "추가", "제거"])

        # Interest Area Inquiry
        with tab1:
            st.subheader("관심영역 조회")
            if st.toggle("사용설명서_조회"):
                st.write(""" 
                        관심영역 조회 기능 사용설명서
                            
                            조회하고자 하는 관심영역을 선택한 후, '관심 영역 조회' 버튼을 누르면 해당 영역이 지도에 표시됩니다.
           """)
            tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
            attr = "Vworld"
            m = folium.Map(location=[36.6384, 127.6961], zoom_start=7,tiles=tiles, attr=attr)
            folium.TileLayer(
            tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
            attr='VWorld Hybrid',
            name='VWorld Hybrid',
            overlay=True
            ).add_to(m)
            selected_aoi_name = st.selectbox('**관심영역 선택**',["조회할 관심영역을 선택하세요."] + aoi_names)
            selected_aoi = next((feature for feature in geojson_data["features"]
                                if feature["properties"]["name"] == selected_aoi_name), None)
            
            if st.button('**관심영역 조회**'):
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
                    st.error("선택된 관심영역을 찾을 수 없습니다.")
            # Displaying a Map in a Streamlet
            folium_static(m)
            

        # Add New AOI tab
        with tab2:
            st.subheader("관심영역 추가")
            if st.toggle("사용설명서_추가"):
                st.write("""
                        관심영역 추가 기능 사용설명서
                                        
                            1. 지도 왼쪽 도형 그리기를 사용하여 원하는 모양의 영역을 드래그합니다.
                            2. 지도 오른쪽 Export 버튼을 통해 .geojson 파일을 다운로드 받습니다.
                            3. 오른쪽 탭에서 '관심영역 이름'작성 후 다운받은 .geojson 파일을 '새로운 관심 영역 파일'에 업로드합니다.
                            4. '관심영역 추가' 버튼을 누르면 새로운 영역이 저장됩니다.
                         
            """)
            col1,col2 = st.columns([0.7,0.3])            
            with col1 : 
                tiles = f"http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/{layer}/{{z}}/{{y}}/{{x}}.{tileType}"
                attr = "Vworld"

                mp = folium.Map(location=[36.6384, 127.6961], zoom_start=7, tiles=tiles, attr=attr)
                folium.TileLayer(
                tiles=f'http://api.vworld.kr/req/wmts/1.0.0/{vworld_key}/Hybrid/{{z}}/{{y}}/{{x}}.png',
                attr='VWorld Hybrid',
                name='VWorld Hybrid',
                overlay=True
                ).add_to(mp)

                # Adding a Draw Plug-in to a Folium Map.
                draw = Draw(export=True)
                mp.add_child(draw)

                # Displaying a Map in a Streamlet
                folium_static(mp)
                
            with col2 : 
                with st.form("관심영역 추가 폼") : 
                    new_aoi_name = st.text_input("**관심영역 이름을 입력하세요**")
                    new_aoi_file = st.file_uploader("**새로운 관심영역의 파일을 업로드하세요**", type=["geojson"])
                    if st.form_submit_button("**관심영역 추가**"):
                        if not new_aoi_name:
                            st.error("관심영역 이름을 입력해야 합니다.")
                        elif not new_aoi_file:
                            st.error("새로운 관심영역 파일을 업로드해야 합니다.")
                        else:
                            new_aoi_data = json.load(BytesIO(new_aoi_file.getvalue()))
                            new_aoi_data["features"][0]["properties"]["name"] = new_aoi_name
                            geojson_data['features'].append(new_aoi_data["features"][0])
                            with open(geojson_path, 'w', encoding='utf-8') as f:
                                json.dump(geojson_data, f, ensure_ascii=False, indent=4)
                            st.success(f"'{new_aoi_name}' 관심영역이 성공적으로 추가되었습니다.")
                            aoi_names.append(new_aoi_name)  # Updated aoi_names list

        # Remove AOI tab
        with tab3:
            st.subheader("관심영역 제거")
            if st.toggle("사용설명서_제거"):
                st.write("""    
                        관심영역 제거 기능 사용설명서
                            
                            제거하고자 하는 관심영역을 선택한 후, '관심영역 제거' 버튼을 누르면 해당 영역 제거됩니다.
                         
            """)
            selected_aoi_name_to_remove = st.selectbox('**관심영역 선택**', ["제거할 관심영역을 선택하세요."] + aoi_names)
            if st.button('**관심영역 제거**') and selected_aoi_name_to_remove != "제거할 관심영역을 선택하세요.":
                geojson_data["features"] = [feature for feature in geojson_data["features"]
                                            if feature["properties"]["name"] != selected_aoi_name_to_remove]
                with open(geojson_path, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, ensure_ascii=False, indent=4)
                st.success(f"'{selected_aoi_name_to_remove}' 관심영역이 성공적으로 제거되었습니다.")
                aoi_names.remove(selected_aoi_name_to_remove)  # Updated aoi_names list
                

# launch
if __name__  == "__main__" :
    app()
    
    