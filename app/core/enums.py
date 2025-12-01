from enum import Enum

class FileMimeType(str, Enum):
    tiff = "image/tiff"
    tif = "image/tiff"
    png = "image/png"
    jpg = "image/jpeg"
    jpeg = "image/jpeg"
    geojson = "application/geo+json"
    json = "application/json"
    shp = "application/octet-stream"
    shapefile = "application/octet-stream"
    zip = "application/zip"
    pdf = "application/pdf"
    
