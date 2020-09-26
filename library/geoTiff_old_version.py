from osgeo import gdal
from osgeo import osr
import numpy as np 
import os, sys
from random import seed,uniform
from tensorflow.keras.models import load_model
import json
import cv2

def getImageBing(name,latitude,longitude,SaveLoc):
    key = "Aqk4d8d5q_eWvI3oGYPNI-NdIuS5fEt3U-AnDWxNAzyM2Dn_v2vn2BbgD_8F-jIh"
    link = f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{latitude},{longitude}/19?mapSize=500,500&key={key}"
    file = name + ".png"
    urllib.request.urlretrieve(link, os.path.join(SaveLoc,file))
    
def meters_to_lon(meters,latitude):
    latitude = math.radians(latitude)
    longitude_meters = 111412.84*cos(latitude) - 93.5 * cos(3*latitude) + 0.118*cos(5*latitude)
    return meters/longitude_meters

def meters_to_lat(meters,latitude):
    
    latitude = math.radians(latitude)
    latitude_meters = 111132.92 - 559.82 * cos(2*latitude) + 1.175*cos(4*latitude) - 0.0023*cos(6*latitude)
    return meters/latitude_meters


class danger():
    error = 0
    no_danger = 1
    level1 = 2
    level2 = 3
    level3 = 4

def read_settings(f):
    with open(f) as fp:
        settings = json.load(fp)['settings']
    model1 = settings['model1']
    model2 = settings['model2']
    autoencoder = settings['autoencoder']
    cell_x = settings["cell_size_x"]
    cell_y = settings["cell_size_y"]

    model1 = load_model(model1)
    model2 = load_model(model2)
    autoencoder = load_model(autoencoder)

    return (model1,model2,autoencoder,cell_x,cell_y)

def calc_risk_img(img,model1,model2,accuracy="low"):
    low_precision_risk = model1.predict(img)
    print(low_risk)
    if(accuracy == "low"):
        return low_precision_risk
    else:
        if low_precision_risk == 0:
            return low_precision_risk

        else:
            high_precision_risk = model2.predict(img)
            return high_precision_risk

def get_img_loc(img,grid_sizex,grid_sizey,height,width,lat_max,lat_min,lon_max,lon_min,lon,lat):
    
    latmin_rat = (lat  - lat_min) / (lat_max - lat_min) 
    lonmin_rat = (lon - lon_min) / (lon_max - lon_min)

    latmax_rat = (lat + meters_to_lat(grid_sizey,lat) - lat_min) / (lat_max - lat_min)
    lonmax_rat = (lon + meters_to_lon(grid_sizex,lat) - lon_min) / (lon_max - lon_min)

    img_min_height = min(latmin_rat * height, height)
    img_max_height = min(latmax_rat * height,height)

    
    img_min_width = min(lonmin_rat * width, width)
    img_max_width = min(lonmax_rat * width, width)

    new_img = img[img_min_height:img_max_height,img_min_width:img_max_width]

    return (new_img,img_min_height,img_min_width,img_max_height,img_max_width)   

def calculate_risks(img,grid_sizex,grid_sizey,height,
                        width,lat_max,lat_min,lon_max,lon_min,
                            model1,model1,accuracy="low"):


    risks = dict()

    curr_lat = lat_min

    while(curr_lat < lat_max):
        curr_lon = lon_min
        
        lon_incr =  meters_to_lon(grid_sizey,curr_lat)
        lat_incr =  meters_to_lat(grid_sizex,curr_lat) 

        while(curr_lon < lon_max):
            new_img,min_height,min_width,max_height,max_width = get_img_loc(img,grid_sizex,grid_sizey,
                height,width,lat_max,lat_min,lon_max,lon_min,curr_lon,curr_lat)
            
            risk = calc_risk_img(img,model1,model2,accuracy)
            
            if not risk in risks:
                risks[risk] = list()

            risks[risk].append((min_height,min_width,max_height,max_width))

            curr_lon += lon_incr

        curr_lat += lat_incr

    return risks
    
def position_risk(risk_low_acc,risk_high_acc,lat,lon,accuracy="low"):
    if accuracy == "low":
        return int(uniform(0,2))
    else:
        return int(uniform(0,5))


def get_coordinates(height,width,x,y,lat_max,lat_min,lon_max,lon_min):
    portion_x = x / width
    portion_y = y / height

    lat = y * (lat_max - lat_min)
    lon = x * (lon_max - lon_min)

    return (lat,lon)
    
def zoning_delimitations(height,width,x,y,lat_max,lat_min,lon_max,lon_min):
    safe = list()
    danger = list()
    level1 = list()
    level2 = list()
    level3 = list()


    
def create_geoTiff(image_size = (1024,1024),lat=(36,41),lon=(-7,-5),filename="default.tif",risks):
    
    lat_min,lat_max = lat
    lon_min,lon_max = lon
    height,width = image_size

    r_pixels = np.zeros((image_size),dtype=np.uint8)
    g_pixels = np.zeros((image_size),dtype=np.uint8)
    b_pixels = np.zeros((image_size),dtype=np.uint8)

    colors = {danger.error: (0,0,0),danger.no_danger: (0, 153, 255),
                danger.level1: (255, 255, 102),danger.level2: (255, 102, 0),
                    danger.level3: (255, 0, 0)}


    for risk in risks:
        for cell in risks[risk]:
            min_height,min_width,max_height,max_width = cell
            
            for x in range(min_width,max_width):
                for y in range(min_height,max_height):
                    r,g,b = colors.get(risk,(255,255,255))
                    r_pixels[y,x] = r
                    g_pixels[y,x] = g
                    b_pixels[y,x] = b

    xres = (lon_max - lon_min) / width
    yres = (lat_max - lat_min) / height

    print(r_pixels)
    print(g_pixels)
    print(b_pixels)
    
    geotransform = (lon_min, xres, 0, lat_max, 0, -yres)

    
    dst_ds = gdal.GetDriverByName('GTiff').Create(filename, width, height, 3, gdal.GDT_Byte)
    
    dst_ds.SetGeoTransform(geotransform)         
    srs = osr.SpatialReference()            
    srs.ImportFromEPSG(3857)                
    dst_ds.SetProjection(srs.ExportToWkt()) 
    dst_ds.GetRasterBand(1).WriteArray(r_pixels)   
    dst_ds.GetRasterBand(2).WriteArray(g_pixels)   
    dst_ds.GetRasterBand(3).WriteArray(b_pixels)   
    dst_ds.FlushCache()                  
    dst_ds = None

def get_square(geofile):
    
    with open(geofile) as f:
        geodict = json.load(f)
    lon_min,lon_max,lat_min,lat_max = math.inf,-math.inf,math.inf,-math.inf
    
    for i in geodict['features'][0]['geometry']['coordinates'][0]:
        print(i)
        if i[0] < lon_min: lon_min=i[0]
        if i[0] > lon_max: lon_max=i[0]
        if i[1] < lat_min: lat_min=i[1]
        if i[1] > lat_max: lat_max=i[1]
    
    
    return (lon_min,lon_max,lat_min,lat_max)

##create_geoTiff(image_size=(2048,512))

def RiskMapFromGeoJson(GeoFile,out_loc=None,size=(512,512),out="GeoTiff"):
    
    lon_min,lon_max,lat_min,lat_max = get_square(GeoFile)
    risks = calculate_risks(img,grid_sizex,grid_sizey,height,
                        width,lat_max,lat_min,lon_max,lon_min,
                            model1,model1,accuracy="low")
    if out == "GeoTiff":

    else:       
    
def main():
    #model1,model2,autoencoder,cell_x,cell_y = read_settings("settings.json")
    print("1")
    print(read_settings("settings.json"))

main()