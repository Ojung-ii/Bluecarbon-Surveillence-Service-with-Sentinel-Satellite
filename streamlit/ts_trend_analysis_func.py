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

# GeoJSON 구조를 사용하여 AOI 설정
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
            scale=10  
        ).get('ndvi')
        return ee.Feature(None, {'ds': date, 'y': mean_ndvi})
    time_series_ndvi = sentinel2.map(calculate_ndvi)
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    rvi_features = time_series_ndvi.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    return df

def calculateFAI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date)\
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # NDVI 계산 및 시계열 데이터 생성 함수
    def calculate_fai(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        lambda_nir = 832.8
        lambda_red = 664.6
        lambda_swir1 = 1613.7

        # Sentinel-2 밴드 선택
        red = image.select('B4')   # Red 밴드
        nir = image.select('B8')   # NIR 밴드
        swir1 = image.select('B11') # SWIR1 밴드
        # FAI 계산
        fai = nir.subtract(red).add(
            swir1.subtract(red).multiply(
                (lambda_nir - lambda_red) / (lambda_swir1 - lambda_red)
            )
        )
        mean_fai = fai.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  
        ).get('ndvi')
        return ee.Feature(None, {'ds': date, 'y': mean_fai})
    time_series_ndvi = sentinel2.map(calculate_fai)
    # 결과를 서버측 객체로 변환 (Python 클라이언트로 가져오기 위함)
    rvi_features = time_series_ndvi.getInfo()['features']
    # 결과를 pandas DataFrame으로 변환
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    return df

def calculateWAVI(aoi, start_date, end_date):
    # Sentinel-2 ImageCollection 필터링 및 구름 마스킹 적용
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
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
            scale=10  
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
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
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
            scale=10  
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
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # WEVI 계산 및 시계열 데이터 생성 함수
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
            scale=10  
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
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # WTDVI 계산 및 시계열 데이터 생성 함수
    def calculate_wtdvi(image):
        green = image.select('B3') # 녹색 밴드
        blue = image.select('B2')  # 파란색 밴드
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        wtdvi = green.subtract(blue).divide(ee.Image(green.pow(2).add(blue).add(0.5)).sqrt()).multiply(1.5).rename('WTDVI')
        mean_wavi = wtdvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10
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
    # Prophet
    # m = Prophet(yearly_seasonality=True,daily_seasonality=False,weekly_seasonality=False,holidays_prior_scale=0,changepoint_prior_scale=0.5)
    m = Prophet(yearly_seasonality=True,daily_seasonality=False,weekly_seasonality=False,holidays_prior_scale=0.01,changepoint_prior_scale=0.01)
    m.fit(df)
    # future dataframe 생성
    future = m.make_future_dataframe(periods=0,freq='M')
    # predict
    forecast = m.predict(future) 
    forecasted_value = forecast.iloc[-1]['yhat']  # 예측된 값을 가져옴
    # 예측 결과를 데이터프레임에 추가
    new_row = pd.DataFrame({'ds': [future.iloc[-1]['ds']], 'y': [forecasted_value]})
    forecast_df = pd.concat([df, new_row], ignore_index=True)
    return forecast,forecast_df,df,m

def plotly(df, forecast):
    forecast = forecast.rename(columns = {'ds':"기간","yhat":"지수"})
    df = df.rename(columns = {'ds':"기간","y":"지수"})
    # 예측 데이터 그래프 생성
    combined_fig = px.line(forecast, x='기간', y='지수', title='예측')
    # 관측 데이터 그래프 추가
    combined_fig.add_trace(px.scatter(df, x='기간', y='지수', title='관측치', color_discrete_sequence=['red']).data[0])
    # 생성된 combined_fig 그래프를 st.plotly_chart()를 사용하여 화면에 표시하기
    st.plotly_chart(combined_fig, use_container_width = True)

import pandas as pd

def ts_analysis(df):
    # 날짜 컬럼을 datetime 형식으로 변환
    df['ds'] = pd.to_datetime(df['ds'])

    # 최대값과 최소값의 일자 찾기
    max_date = df[df['yhat'] == df['yhat'].max()]['ds'].iloc[0]
    min_date = df[df['yhat'] == df['yhat'].min()]['ds'].iloc[0]

    # 계절을 구분하기 위한 함수 정의
    def get_season(month):
        if month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        elif month in [9, 10, 11]:
            return 'Fall'
        else:
            return 'Winter'

    # 월별 계절 할당
    df['season'] = df['ds'].dt.month.apply(get_season)

    # 계절별 평균값 계산
    seasonal_trend = df.groupby('season')['yhat'].mean()

    # 매월 평균 계산
    monthly_avg = df.groupby(df['ds'].dt.month)['yhat'].mean()

    # 전체 기간에 대한 평균 yhat 값
    overall_avg = df['yhat'].mean()

    # 계절별 평균값을 전체 평균값으로 나누어 상대적인 비율 계산
    seasonal_relative = seasonal_trend / overall_avg

    # 매년 평균값 계산
    annual_avg = df.groupby(df['ds'].dt.year)['yhat'].mean()

    # 매년 평균값을 전체 평균값으로 나누어 상대적인 비율 계산
    annual_relative = annual_avg / overall_avg

    # 매월 평균값을 전체 평균값으로 나누어 상대적인 비율 계산
    monthly_relative = monthly_avg / overall_avg

    result_df = pd.DataFrame({'seasonal_relative': seasonal_relative,
                              'annual_relative': annual_relative,
                              'monthly_relative': monthly_relative
    })

    return result_df, max_date, min_date, seasonal_trend
