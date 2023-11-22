import ee
import pandas as pd
from prophet import Prophet
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import folium

# folium맵에 GEE 레이어 추가
def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles = map_id_dict['tile_fetcher'].url_format,
        attr = 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name = name,
        overlay = True,
        control = True
    ).add_to(self)

'''
1. p_values 함수를 호출
2. P 값 배열을 계산하고
3. 이 배열을 사용하여 filter_i 및 filter_j 함수를 통해 변화 지도를 생성
4. dmap_iter 함수를 사용하여 변화 방향(증가, 감소, 무한한증가)을 결정
cmap: 가장 최근의 변화 간격, 한 밴드
smap: 첫 번째 변경 간격, 한 대역
fmap: 변경 횟수, 한 대역
bmap: 각 간격의 변화
'''

# 감마 함수를 이용해서 카이제곱분포 CDF계산
def chi2cdf(chi2, df2):
    return ee.Image(chi2.divide(2)).gammainc(ee.Number(df2).divide(2))

#통계적 검증에 사용될 공분산 행렬식
def det(im):
    return im.expression('b(0)*b(1)')

#이미지 리스트의 첫 번째부터 j번째 이미지까지의 합의 행렬식(log determinant)의 로그 값을 계산
def log_det_sum(im_list, j):
    im_ist = ee.List(im_list)
    sumj = ee.ImageCollection(im_list.slice(0, j)).reduce(ee.Reducer.sum())
    return ee.Image(det(sumj)).log()

# 이미지 리스트에서 j번째 이미지의 로그 행렬식 계
def log_det(im_list, j):
    im = ee.Image(ee.List(im_list).get(j.subtract(1)))
    return ee.Image(det(im)).log()

# im_list에 대한 P-value와 -2logRj 계산 -> 여기 -2logRj는 두 확률 분포의 차이, 즉 두 이미지 사이의 변화를 평가하는데 사용됨.
def pval(im_list, j, m=4.4):
    im_list = ee.List(im_list)
    j = ee.Number(j)
    m2logRj = (log_det_sum(im_list, j.subtract(1))
               .multiply(j.subtract(1))
               .add(log_det(im_list, j))
               .add(ee.Number(2).multiply(j).multiply(j.log()))
               .subtract(ee.Number(2).multiply(j.subtract(1))
               .multiply(j.subtract(1).log()))
               .subtract(log_det_sum(im_list,j).multiply(j))
               .multiply(-2).multiply(m))
    pv = ee.Image.constant(1).subtract(chi2cdf(m2logRj, 2))
    return (pv, m2logRj)

#이미지 리스트에 대한 P 값 배열 사전 계산
def p_values(im_list):
    im_list = ee.List(im_list)
    k = im_list.length()

    #이번에 들어온 집합에 대한 계산
    def ells_map(ell):
        ell = ee.Number(ell)
        im_list_ell = im_list.slice(k.subtract(ell), k)

        def js_map(j):
            j = ee.Number(j)
            pv1, m2logRj1 = pval(im_list_ell, j)
            return ee.Feature(None, {'pv': pv1, 'm2logRj': m2logRj1})

        js = ee.List.sequence(2, ell)
        pv_m2logRj = ee.FeatureCollection(js.map(js_map))
        m2logQl = ee.ImageCollection(pv_m2logRj.aggregate_array('m2logRj')).sum()
        pvQl = ee.Image.constant(1).subtract(chi2cdf(m2logQl, ell.subtract(1).multiply(2)))
        pvs = ee.List(pv_m2logRj.aggregate_array('pv')).add(pvQl)
        return pvs
    ells = ee.List.sequence(k, 2, -1)
    pv_arr = ells.map(ells_map)
    return pv_arr

#filter_i에 의해 호출되며, pv_arr의 각 행 내에서 개별 요소(열)에 대한 반복 작업을 수행
def filter_j(current, prev):
    """Calculates change maps; iterates over j indices of pv_arr."""
    pv = ee.Image(current)
    prev = ee.Dictionary(prev)
    pvQ = ee.Image(prev.get('pvQ'))
    i = ee.Number(prev.get('i'))
    cmap = ee.Image(prev.get('cmap'))#어떤 지역에서 변화가 발생했는지를 나타내는 지도
    smap = ee.Image(prev.get('smap'))#변화가 얼마나 자주 발생했는지를 나타내는 지도
    fmap = ee.Image(prev.get('fmap'))#변화가 발생한 순서를 나타내는 지도
    bmap = ee.Image(prev.get('bmap'))#변화가 발생한 방향을 나타내는 지도
    alpha = ee.Image(prev.get('alpha'))
    j = ee.Number(prev.get('j'))
    cmapj = cmap.multiply(0).add(i.add(j).subtract(1))

    #현재 P 값(pv)과 누적 P 값(pvQ)이 모두 임계값(alpha)보다 작은지 확인. 이것이 참이면 변화가 감지된 것으로 간주.
    tst = pv.lt(alpha).And(pvQ.lt(alpha)).And(cmap.eq(i.subtract(1)))

    cmap = cmap.where(tst, cmapj)
    fmap = fmap.where(tst, fmap.add(1))
    smap = ee.Algorithms.If(i.eq(1), smap.where(tst, cmapj), smap)

    idx = i.add(j).subtract(2)
    tmp = bmap.select(idx)
    bname = bmap.bandNames().get(idx)
    tmp = tmp.where(tst, 1)
    tmp = tmp.rename([bname])

    #실제로 변화탐지가 방향성까지 고려되어 표시된 지도가 bmap
    bmap = bmap.addBands(tmp, [bname], True)
    return ee.Dictionary({'i': i, 'j': j.add(1), 'alpha': alpha, 'pvQ': pvQ,
                          'cmap': cmap, 'smap': smap, 'fmap': fmap, 'bmap':bmap})

# filter_j 함수를 호출하여 변화를 탐지
def filter_i(current, prev):
    current = ee.List(current)
    pvs = current.slice(0, -1 )
    pvQ = ee.Image(current.get(-1))
    prev = ee.Dictionary(prev)
    i = ee.Number(prev.get('i'))
    alpha = ee.Image(prev.get('alpha'))
    median = prev.get('median')

    pvQ = ee.Algorithms.If(median, pvQ.focalMedian(2.5), pvQ)
    cmap = prev.get('cmap')
    smap = prev.get('smap')
    fmap = prev.get('fmap')
    bmap = prev.get('bmap')
    first = ee.Dictionary({'i': i, 'j': 1, 'alpha': alpha ,'pvQ': pvQ,
                           'cmap': cmap, 'smap': smap, 'fmap': fmap, 'bmap': bmap})
    result = ee.Dictionary(ee.List(pvs).iterate(filter_j, first))
    return ee.Dictionary({'i': i.add(1), 'alpha': alpha, 'median': median,
                          'cmap': result.get('cmap'), 'smap': result.get('smap'),
                          'fmap': result.get('fmap'), 'bmap': result.get('bmap')})


# 방향성 변화 지도의 값을 재분류하고, bmap에 반영 (평균이지미avimg 계속 업데이트)
def dmap_iter(current, prev):
    prev = ee.Dictionary(prev)
    j = ee.Number(prev.get('j'))
    image = ee.Image(current)
    avimg = ee.Image(prev.get('avimg'))
    diff = image.subtract(avimg)
    
    #변화(긍정, 부정) 계산
    posd = ee.Image(diff.select(0).gt(0).And(det(diff).gt(0)))
    negd = ee.Image(diff.select(0).lt(0).And(det(diff).gt(0)))
    bmap = ee.Image(prev.get('bmap'))
    bmapj = bmap.select(j)
    dmap = ee.Image.constant(ee.List.sequence(1, 3))
    bmapj = bmapj.where(bmapj, dmap.select(2))
    bmapj = bmapj.where(bmapj.And(posd), dmap.select(0))
    bmapj = bmapj.where(bmapj.And(negd), dmap.select(1))
    bmap = bmap.addBands(bmapj, overwrite=True)

    i = ee.Image(prev.get('i')).add(1)
    avimg = avimg.add(image.subtract(avimg).divide(i))#계속해서 평균이미지 업데이트

    avimg = avimg.where(bmapj, image)
    i = i.where(bmapj, 1)
    return ee.Dictionary({'avimg': avimg, 'bmap': bmap, 'j': j.add(1), 'i': i})

#im_list에 대한 종류별 변화 지도를 계산
def change_maps(im_list, median=False, alpha=0.01):
    k = im_list.length()

    pv_arr = ee.List(p_values(im_list))

    cmap = ee.Image(im_list.get(0)).select(0).multiply(0)
    bmap = ee.Image.constant(ee.List.repeat(0,k.subtract(1))).add(cmap)
    alpha = ee.Image.constant(alpha)
    first = ee.Dictionary({'i': 1, 'alpha': alpha, 'median': median,
                           'cmap': cmap, 'smap': cmap, 'fmap': cmap, 'bmap': bmap})
    result = ee.Dictionary(pv_arr.iterate(filter_i, first))

    bmap =  ee.Image(result.get('bmap'))
    avimg = ee.Image(im_list.get(0))
    j = ee.Number(0)
    i = ee.Image.constant(1)
    first = ee.Dictionary({'avimg': avimg, 'bmap': bmap, 'j': j, 'i': i})
    dmap = ee.Dictionary(im_list.slice(1).iterate(dmap_iter, first)).get('bmap')#시점별로 지도생성
    return ee.Dictionary(result.set('bmap', dmap))
