import ee
import pandas as pd
from prophet import Prophet
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import folium

# Earth Engine API initialization
ee.Initialize()

# Set up AOI using GeoJSON structure
def create_ee_polygon_from_geojson(gjson):
    coordinates = gjson['geometry']['coordinates']
    aoi = ee.Geometry.Polygon(coordinates)
    return aoi

def calculateRVI(aoi,start_date,end_date):
    # Sentinel-1 ImageCollection filtering
    sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
    # RVI calculation and time series data frame generation functions
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
    # Calculate RVI.
    time_series_rvi = sentinel1.map(calculate_rvi)
    # Convert results to server-side objects. (to import to Python client)
    rvi_features = time_series_rvi.getInfo()['features']
    # Converting Results to Pandas DataFrame.
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    # Sort DataFrame in ascending order according to column 'Date'.
    df = df.sort_values(by='ds')
    return df

def calculateNDVI(aoi, start_date, end_date):
    # Applying filtering and cloud masking to Sentinel-2 Image Collection
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date)\
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # NDVI calculation and time series data frame generation functions
    def calculate_ndvi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        nir = image.select('B8')  # NIR(Near-Infrared Spectrometer) vand 
        red = image.select('B4')  # Red vand
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi')
        mean_ndvi = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  
        ).get('ndvi')
        return ee.Feature(None, {'ds': date, 'y': mean_ndvi})
    time_series_ndvi = sentinel2.map(calculate_ndvi)
    # Convert results to server-side object (to import to Python client)
    rvi_features = time_series_ndvi.getInfo()['features']
    # Converting Results to Pandas DataFrame.
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    return df

def calculateFAI(aoi, start_date, end_date):
    # Applying filtering and cloud masking to Sentinel-2 Image Collection
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date)\
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # NDVI calculation and time series data frame generation functions
    def calculate_fai(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        lambda_nir = 832.8
        lambda_red = 664.6
        lambda_swir1 = 1613.7

        # Selecting vand.
        red = image.select('B4')   # Red vand
        nir = image.select('B8')   # NIR vand
        swir1 = image.select('B11') # SWIR1 vand
        # Calculate FAI
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
    # Convert results to server-side object (to import to Python client)
    rvi_features = time_series_ndvi.getInfo()['features']
    # Converting Results to Pandas DataFrame.
    df = pd.DataFrame([feat['properties'] for feat in rvi_features])
    return df

def calculateWAVI(aoi, start_date, end_date):
    # Filter the Sentinel-2 ImageCollection and apply cloud masking
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    
    # Function to calculate WAVI and create time series data
    def calculate_wavi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        nir = image.select('B8')  # NIR band
        red = image.select('B4')  # Red band
        wavi = nir.subtract(red).divide(nir.add(red).add(0.1)).rename('wavi')  # Using L value of 0.1
        mean_wavi = wavi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  
        ).get('wavi')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})

    time_series_wavi = sentinel2.map(calculate_wavi)
    # Convert results to server-side object (to retrieve on Python client)
    wavi_features = time_series_wavi.getInfo()['features']
    # Convert results to pandas DataFrame
    df = pd.DataFrame([feat['properties'] for feat in wavi_features])
    # Sort DataFrame by 'Date' column in ascending order
    df = df.sort_values(by='ds')
    return df

def calculateDIFF_BG(aoi, start_date, end_date):
    # Filter the Sentinel-2 ImageCollection and apply cloud masking
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # Function to calculate the difference between blue and green bands (Diff(B-G)) and create time series data
    def calculate_diff_bg(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        blue = image.select('B2')  # Bluse band
        green = image.select('B3') # Green band
        diff_bg = blue.subtract(green).rename('Diff_BG')
        mean_wavi = diff_bg.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  
        ).get('Diff_BG')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    time_series_diff_bg = sentinel2.map(calculate_diff_bg)
    # Convert results to server-side object (to retrieve on Python client)
    diff_bg_features = time_series_diff_bg.getInfo()['features']
    # Convert results to pandas DataFrame
    df = pd.DataFrame([feat['properties'] for feat in diff_bg_features])
    # Sort DataFrame by 'Date' column in ascending order
    df = df.sort_values(by='ds')
    return df

def calculate_WEVI(aoi, start_date, end_date):
    # Filter the Sentinel-2 ImageCollection and apply cloud masking
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    # Function to calculate WEVI (Water-Enhanced Vegetation Index) and create time series data
    def calculate_wevi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        green = image.select('B3') # Green band
        red = image.select('B4')   # Red band
        blue = image.select('B2')  # Blue band
        # Modified WEVI calculation
        wevi = green.subtract(red).divide(green.add(red).subtract(red.multiply(6)).add(blue.multiply(7.5)).add(1)).multiply(2.5).rename('WEVI')
        mean_wavi = wevi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10  
        ).get('WEVI')
        return ee.Feature(None, {'ds': date, 'y': mean_wavi})
    time_series_wevi = sentinel2.map(calculate_wevi)
    # Convert results to server-side object (to retrieve on Python client)
    wevi_features = time_series_wevi.getInfo()['features']
    # Convert results to pandas DataFrame
    df = pd.DataFrame([feat['properties'] for feat in wevi_features])
    # Sort DataFrame by 'Date' column in ascending order
    df = df.sort_values(by='ds')
    return df

def calculate_WTDVI(aoi, start_date, end_date):
    # Filter the Sentinel-2 ImageCollection and apply cloud masking
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    
    # Function to calculate WTDVI (Weighted Difference Vegetation Index) and create time series data
    def calculate_wtdvi(image):
        date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
        green = image.select('B3') # Green band
        blue = image.select('B2')  # Blue band
        # Calculation of WTDVI
        wtdvi = green.subtract(blue).divide(ee.Image(green.pow(2).add(blue).add(0.5)).sqrt()).multiply(1.5).rename('WTDVI')
        mean_wtdvi = wtdvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10
        ).get('WTDVI')
        return ee.Feature(None, {'ds': date, 'y': mean_wtdvi})

    time_series_wtdvi = sentinel2.map(calculate_wtdvi)
    # Convert results to server-side object (to retrieve on Python client)
    wtdvi_features = time_series_wtdvi.getInfo()['features']
    # Convert results to pandas DataFrame
    df = pd.DataFrame([feat['properties'] for feat in wtdvi_features])
    # Sort DataFrame by 'Date' column in ascending order
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
    # Rename columns in forecast and df for clarity
    forecast = forecast.rename(columns={'ds': "Period", 'yhat': "Index"})
    df = df.rename(columns={'ds': "Period", 'y': "Index"})

    # Create a line plot for the forecast data
    combined_fig = px.line(forecast, x='Period', y='Index', title='Forecast')
    
    # Add observational data as scatter plot on the same graph
    combined_fig.add_trace(px.scatter(df, x='Period', y='Index', title='Observations', color_discrete_sequence=['red']).data[0])
    
    # Display the combined figure using Streamlit's plotly_chart function
    st.plotly_chart(combined_fig, use_container_width=True)

def ts_analysis(df):
    # Convert the date column to datetime format
    df['ds'] = pd.to_datetime(df['ds'])

    # Find the dates of maximum and minimum values
    max_date = df[df['yhat'] == df['yhat'].max()]['ds'].iloc[0]
    min_date = df[df['yhat'] == df['yhat'].min()]['ds'].iloc[0]

    # Define a function to categorize seasons based on month
    def get_season(month):
        if month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        elif month in [9, 10, 11]:
            return 'Fall'
        else:
            return 'Winter'

    # Assign season to each month
    df['season'] = df['ds'].dt.month.apply(get_season)

    # Calculate the average value per season
    seasonal_trend = df.groupby('season')['yhat'].mean()

    # Calculate the average value per month
    monthly_avg = df.groupby(df['ds'].dt.month)['yhat'].mean()

    # Calculate the average yhat value for the entire period
    overall_avg = df['yhat'].mean()

    # Calculate the relative ratio of seasonal averages to overall average
    seasonal_relative = seasonal_trend / overall_avg

    # Calculate the average value per year
    annual_avg = df.groupby(df['ds'].dt.year)['yhat'].mean()

    # Calculate the relative ratio of annual averages to overall average
    annual_relative = annual_avg / overall_avg

    # Calculate the relative ratio of monthly averages to overall average
    monthly_relative = monthly_avg / overall_avg

    return seasonal_relative, annual_relative, monthly_relative, max_date, min_date, seasonal_trend