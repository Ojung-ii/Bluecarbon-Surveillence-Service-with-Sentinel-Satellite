import streamlit as st
import geemap
import ee

# Google Earth Engine 초기화
ee.Initialize()

# Streamlit 앱 제목 설정
st.set_page_config(page_title="변화탐지_확인", page_icon="👀")

st.title('Sentinel-1 타임랩스 생성기')
st.write("---"*20)
# 날짜 형식 변환 함수
def format_date(date_int):
    date_str = str(date_int)
    # YYYYMMDD 형식의 문자열을 YYYY-MM-DD로 변환
    return f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}'

# 사용자 입력 받기
start_date = st.text_input('시작 날짜 (YYYYMMDD 형식)', value='20200101')
end_date = st.text_input('종료 날짜 (YYYYMMDD 형식)', value='20200131')
frequency = st.selectbox('빈도 선택', options=['day', 'month', 'quarter', 'year'])

# 사용자가 제공한 날짜를 변환
formatted_start_date = format_date(int(start_date))
formatted_end_date = format_date(int(end_date))

# Taeanhaean의 ROI 설정
roi = ee.FeatureCollection("WCMC/WDPA/current/polygons") \
    .filter(ee.Filter.eq("NAME", "Sinduri Sand Dune Water")) \
    .geometry().bounds()

# 타임랩스 생성 버튼
if st.button('타임랩스 생성'):
    with st.spinner('타임랩스를 생성하는 중입니다...'):
        try:
            # 타임랩스 생성 로직
            output_gif = './timelapse.gif'  # 타임랩스를 저장할 경로와 파일명
            
            # geemap.sentinel1_timelapse 함수 호출
            timelapse = geemap.sentinel1_timelapse(
                roi=roi,
                out_gif=output_gif,
                start_year=int(start_date[:4]),
                end_year=int(end_date[:4]),
                start_date=f"{start_date[4:6]}-{start_date[6:]}",  
                end_date=f"{end_date[4:6]}-{end_date[6:]}",
                frequency=frequency,
                date_format=None,
                palette='Greys',
                vis_params=None,
                dimensions=768,
                frames_per_second=1,
                crs='EPSG:3857',
                overlay_data=None,
                overlay_color='black',
                overlay_width=1,
                overlay_opacity=1.0,
                title=None,
                title_xy=('2%', '90%'),
                add_text=True,
                text_xy=('2%', '2%'),
                text_sequence=None,
                font_type='arial.ttf',
                font_size=20,
                font_color='white',
                add_progress_bar=True,
                progress_bar_color='blue',
                progress_bar_height=5,
                add_colorbar=False,
                colorbar_width=6.0,
                colorbar_height=0.4,
                colorbar_label=None,
                colorbar_label_size=12,
                colorbar_label_weight='normal',
                colorbar_tick_size=10,
                colorbar_bg_color=None,
                colorbar_orientation='horizontal',
                colorbar_dpi='figure',
                colorbar_xy=None,
                colorbar_size=(300, 300),
                loop=0, mp4=False,
                fading=False,
                orbitProperties_pass='DESCENDING'
            )
            
            # 타임랩스 이미지 표시
            st.image(output_gif, caption='Sentinel-1 타임랩스', use_column_width=True)

        except Exception as e:
            st.error(f'타임랩스 생성 중 오류 발생: {e}')
