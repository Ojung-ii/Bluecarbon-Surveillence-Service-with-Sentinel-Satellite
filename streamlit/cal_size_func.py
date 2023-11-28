import ee
import pandas as pd
import folium

CLOUD_FILTER = 60
CLD_PRB_THRESH = 40
NIR_DRK_THRESH = 0.15
CLD_PRJ_DIST = 2
BUFFER = 100

def get_s2_sr_cld_col(aoi, start_date, end_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CLOUD_FILTER)))


    # Import and filter s2cloudless.
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))

def apply_cld_shdw_mask(img):
    # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
    not_cld_shdw = img.select('cloudmask').Not()

    # Subset reflectance bands and update their masks, return the result.
    return img.select('B.*').updateMask(not_cld_shdw)

def add_cloud_bands(img):
    # Get s2cloudless image, subset the probability band.
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # Condition s2cloudless by the probability threshold value.
    is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))

def add_shadow_bands(img):
    # Identify water pixels from the SCL band.
    not_water = img.select('SCL').neq(6)

    # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(NIR_DRK_THRESH*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, CLD_PRJ_DIST*10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))

    # Identify the intersection of dark pixels with cloud shadow projection.
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')

    # Add dark pixels, cloud projection, and identified shadows as image bands.
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

def add_cld_shdw_mask(img):
    # Add cloud component bands.
    img_cloud = add_cloud_bands(img)

    # Add cloud shadow component bands.
    img_cloud_shadow = add_shadow_bands(img_cloud)

    # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

    # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
    # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
    is_cld_shdw = (is_cld_shdw.focalMin(2).focalMax(BUFFER*2/20)
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
        .rename('cloudmask'))

    # Add the final cloud-shadow mask to the image.
    return img_cloud_shadow.addBands(is_cld_shdw)

def process_cal_size_1(start_date,end_date,aoi):
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')  # MS는 월의 시작을 의미합니다.

    # 최종 이미지 컬렉션을 생성합니다.
    final_image_collection = ee.ImageCollection([])

    for start in dates:
        end = start + pd.offsets.MonthEnd() + pd.offsets.MonthEnd()
        s2_sr_cld_col = get_s2_sr_cld_col(aoi, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        s2_sr_median = (s2_sr_cld_col.map(add_cld_shdw_mask).map(apply_cld_shdw_mask).median())
        # 최종 이미지 컬렉션에 추가
        final_image_collection = final_image_collection.merge(ee.ImageCollection(s2_sr_median))
    return final_image_collection.first()

def calculate_moisture(img):
    moisture = img.normalizedDifference(['B8A', 'B11'])
    return img.addBands(moisture.rename('moisture'))

def calculate_NDWI(img):
    NDWI = img.normalizedDifference(['B3', 'B8'])
    return img.addBands(NDWI.rename('NDWI'))

def water_bodies_index(img):
    moisture = img.select('moisture')
    NDWI = img.select('NDWI')
    water_bodies = NDWI.subtract(moisture).divide(NDWI.add(moisture))
    return img.addBands(water_bodies.rename('water_bodies'))

def calculate_Fai(image):
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
    ).rename('FAI')
    return image.addBands(fai.rename('FAI'))

def process_image(img):
    img = calculate_moisture(img)
    img = calculate_NDWI(img)
    img = calculate_Fai(img)
    return img

def mask_for_aoi(img, aoi):
    # AOI에 대한 마스크를 생성합니다.
    aoi_mask = ee.Image.constant(1).clip(aoi)
    # 이 마스크를 이미지에 적용합니다.
    return img.updateMask(aoi_mask)

# Earth Engine Python API의 이미지를 Folium 맵에 추가하는 함수를 정의합니다.
def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True
    ).add_to(self)

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
def calculate_area(fai_s2_sr_first_img_parse,aoi):
    fai_mask_1 = fai_s2_sr_first_img_parse.select('FAI').gt(1)
    masked_image_1 = fai_s2_sr_first_img_parse.updateMask(fai_mask_1)
    masked_clip_image_1 = masked_image_1.clip(aoi)
    # 마스킹된 영역의 총 면적 계산
    masked_area_1 = masked_clip_image_1.select('FAI').reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,  # 관심 지역을 지정
        scale=10,  # Sentinel-2 픽셀 해상도
    ).get('FAI')
    # 면적 결과 출력 (제곱미터 단위)
    area_sq_meters_1 = masked_area_1.getInfo()
    return area_sq_meters_1

def calculate_all_area(aoi):
    # Calculate the area of the AOI in square meters.
    area = aoi.area().getInfo()

    # Convert the area to square kilometers (1 square kilometer = 1,000,000 square meters).
    area_sq_km = area / 1_000_000
    return area_sq_km