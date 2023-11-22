import ee
import pandas as pd
from prophet import Prophet
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import folium

# Earth Engine API 초기화
ee.Initialize()
# GeoJSON 구조를 사 용하여 AOI 설정

def create_ee_polygon_from_geojson(gjson):
    coordinates = gjson['geometry']['coordinates']
    aoi = ee.Geometry.Polygon(coordinates)
    return aoi
def calculateRVI(aoi,start_date,end_date):
    # Sentinel-1 ImageCollection 필터링
    sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
    # RVI 계산 및 시계열 데이터 생성 함수
    def calculate_rvi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        vv = image.select('VV')
        vh = image.select('VH')
        rvi = vh.multiply(4).divide(vv.add(vh)).rename('rvi')
        mean_rvi = rvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10
        ).get('rvi')
        return ee.Feature(None, {'ds': date, 'y': mean_rvi})
    # 시계열 RVI 계산
    time_series_rvi = sentinel1.map(calculate_rvi)
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    rvi_features = time_series_rvi.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    # DataFrame을 'Date' 컬럼에 따라 오름차순으로 정렬
    df = df.sort_values(by='ds')
    return df
def calculateNDVI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date)\
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # NDVI 계산 및 시계열 데이터 생성 함수
    def calculate_ndvi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        nir = image.select('B8')  # NIR 밴드
        red = image.select('B4')  # Red 밴드
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi')
        mean_ndvi = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  # 이 값은 필요에 따라 조정할 수 있습니다.
        ).get('ndvi')
        return ee.Feature(None, {'ds': date, 'y': mean_ndvi})
    
    
    time_series_ndvi = sentinel2.map(calculate_ndvi)
    
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    rvi_features = time_series_ndvi.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    return df

def calculateWAVI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    
    # WAVI 계산 및 시계열 데이터 생성 함수
    def calculate_wavi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        nir = image.select('B8')  # NIR 밴드
        red = image.select('B4')  # Red 밴드
        wavi = nir.subtract(red).divide(nir.add(red).add(0.1)).rename('wavi')  # L 값으로 0.1 사용
        mean_wavi = wavi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  # 이 값은 필요에 따라 조정할 수 있습니다.
        ).get('wavi')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    
    time_series_wavi = sentinel2.map(calculate_wavi)
    
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    wavi_features = time_series_wavi.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in wavi_features])
    # DataFrame을 'Date' 컬럼에 따라 오름차순으로 정렬
    df = df.sort_values(by='ds')
    
    return df
def calculateDIFF_BG(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # WAVI 계산 및 시계열 데이터 생성 함수
    def calculate_diff_bg(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        # Diff(B-G) 계산을 위한 함수 정의
        blue = image.select('B2')  # 파란색 밴드
        green = image.select('B3') # 녹색 밴드
        diff_bg = blue.subtract(green).rename('Diff_BG')
        mean_wavi = diff_bg.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  # 이 값은 필요에 따라 조정할 수 있습니다.
        ).get('Diff_BG')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    
    time_series_diff_bg = sentinel2.map(calculate_diff_bg)
    
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    diff_bg_features = time_series_diff_bg.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in diff_bg_features])
    # DataFrame을 'Date' 컬럼에 따라 오름차순으로 정렬
    df = df.sort_values(by='ds')
    
    return df
def calculate_WEVI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # WAVI 계산 및 시계열 데이터 생성 함수
    def calculate_wevi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        green = image.select('B3') # 녹색 밴드
        red = image.select('B4')   # 적색 밴드
        blue = image.select('B2')  # 파란색 밴드
        # 수정된 WEVI 계산
        wevi = green.subtract(red).divide(green.add(red).subtract(red.multiply(6)).add(blue.multiply(7.5)).add(1)).multiply(2.5).rename('WEVI')
        mean_wavi = wevi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  # 이 값은 필요에 따라 조정할 수 있습니다.
        ).get('WEVI')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    
    time_series_diff_bg = sentinel2.map(calculate_wevi)
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    wevi_features = time_series_diff_bg.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in wevi_features])
    # DataFrame을 'Date' 컬럼에 따라 오름차순으로 정렬
    df = df.sort_values(by='ds')
    return df

def calculate_WTDVI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # WAVI 계산 및 시계열 데이터 생성 함수
    def calculate_wtdvi(image):
        green = image.select('B3') # 녹색 밴드
        blue = image.select('B2')  # 파란색 밴드
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        wtdvi = green.subtract(blue).divide(ee.Image(green.pow(2).add(blue).add(0.5)).sqrt()).multiply(1.5).rename('WTDVI')
        mean_wavi = wtdvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  # 이 값은 필요에 따라 조정할 수 있습니다.
        ).get('WTDVI')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    
    time_series_diff_bg = sentinel2.map(calculate_wtdvi)
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    wtdvi_features = time_series_diff_bg.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in wtdvi_features])
    # DataFrame을 'Date' 컬럼에 따라 오름차순으로 정렬
    df = df.sort_values(by='ds')
    
    return df
def prophet_process(df):
    # Prophet 모델을 초기화하고 학습시킵니다.
    # m = Prophet(yearly_seasonality=True,daily_seasonality=False,weekly_seasonality=False,holidays_prior_scale=0,changepoint_prior_scale=0.5)
    m = Prophet(yearly_seasonality=True,daily_seasonality=False,weekly_seasonality=False,holidays_prior_scale=0.01,changepoint_prior_scale=0.01)
    m.fit(df)
    # 미래 날짜 프레임을 만들고 예측을 진행합니다.
    future = m.make_future_dataframe(periods=12,freq='M')
    forecast = m.predict(future) 
    # 예측 결과를 가져옵니다.
    forecasted_value = forecast.iloc[-1]['yhat']  # 예측된 값을 가져옴
    # 예측 결과를 데이터프레임에 추가합니다.
    new_row = pd.DataFrame({'ds': [future.iloc[-1]['ds']], 'y': [forecasted_value]})
    forecast_df = pd.concat([df, new_row], ignore_index=True)
    return forecast,forecast_df,df,m

def plotly(df, forecast):
    forecast = forecast.rename(columns = {'ds':"기간","yhat":"지수"})
    df = df.rename(columns = {'ds':"기간","y":"지수"})
    # Create a Plotly Express figure for both forecast and observed data
    combined_fig = px.line(forecast, x='기간', y='지수', title='예측')
    
    # Add observed data to the same figure
    combined_fig.add_trace(px.scatter(df, x='기간', y='지수', title='관측치', color_discrete_sequence=['red']).data[0])
    # Display the combined figure using st.plotly_chart()
    st.plotly_chart(combined_fig, use_container_width = True)





