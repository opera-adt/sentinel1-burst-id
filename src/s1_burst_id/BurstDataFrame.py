#!/usr/bin/env python3


import json
import os
import datetime                                                                                                                                                   
import xml
import xml.etree.ElementTree as ET
import zipfile
import fnmatch
import pandas as pd
import geopandas as gpd 
from shapely.geometry import Polygon
from s1_burst_id.upload_data import s3UploadDownload



class BurstDataFrame:
    """
    A class to create and update pandas dataframes for burst images.
    """

    def __init__(self, url=None, swath=1):
        """The constructor for BurstDataFrame class.
        Parameters:
            url: the URL of a Sentinel-1 frame
            swath: the swath number of the frame (1,2 or 3)
        """

        self.url = url
        self.swath = swath
        self.df = gpd.GeoDataFrame(columns=['burst_ID', 'pass_direction', 'longitude', 'latitude', 'geometry'])
        self.df_tseries = gpd.GeoDataFrame(columns=['burst_ID', 'date', 'url', 'measurement', 'annotation', 'start', 'end'])

    def getCoordinates(self, zipname):
        """
        The function to extract the Ground Control Points (GCP) of bursts from tiff file.

        Parameters:
            zipname: the name of the zipfile which contains the data

        Returns:
            df_coordinates: A pandas dataframe of GCPs 
        """

        zf = zipfile.ZipFile(zipname, 'r')

        tiffpath = os.path.join('*SAFE','measurement', 's1[ab]-iw{}-slc*tiff'.format(self.swath))
        match = fnmatch.filter(zf.namelist(), tiffpath)
        zf.close()

        tiffname = os.path.join('/vsizip/' + zipname, match[0])
        cmd = "gdalinfo -json {} >> info.json".format(tiffname)
        os.system(cmd)
        with open("info.json", 'r') as fid:
            info = json.load(fid)

        df_coordinates = pd.DataFrame(info['gcps']['gcpList'])
        os.system('rm info.json')
        return df_coordinates, match[0]

    def burstCoords(self, geocoords, lineperburst, idx):
        """
        The function to extract coordinates for a given burst.

        Parameters:
            geocoords: A pandas dataframe of GCPs 
            lineperburst: number of lines in each burst
            idx: index of the burst of interest

        Returns:
            poly: a shapely polygon represnting the boundary of the burst
            xc: longitude of the centroid of the polygon
            yc: latitude of the centroid of the polygon
        """

        firstLine = geocoords.loc[geocoords['line']==idx*lineperburst].filter(['x', 'y'])
        secondLine = geocoords.loc[geocoords['line']==(idx+1)*lineperburst].filter(['x', 'y'])
        X1=firstLine['x'].tolist()
        Y1=firstLine['y'].tolist()
        X2=secondLine['x'].tolist()
        Y2=secondLine['y'].tolist()
        X2.reverse()
        Y2.reverse()
        X = X1 + X2
        Y= Y1 +Y2
        poly = Polygon(zip(X,Y))
        xc, yc = poly.centroid.xy
        return poly, xc[0], yc[0]
      
    def update(self, zipname):
        """
        The function to update the dataframes
        Parameters:
            zipname: the zip file which contains the satellite data 
        """

        zf = zipfile.ZipFile(zipname, 'r')
        xmlpath = os.path.join('*SAFE','annotation', 's1[ab]-iw{}-slc*xml'.format(self.swath))
        match = fnmatch.filter(zf.namelist(), xmlpath)
        xmlstr = zf.read(match[0])
        annotation_path = match[0]
        xml_root = ET.fromstring(xmlstr)
        # Burst interval
        burst_interval = 2.758277

        ascNodeTime = getxmlvalue(xml_root, "imageAnnotation/imageInformation/ascendingNodeTime")
        numBursts = getxmlattr(xml_root, 'swathTiming/burstList', 'count')
        burstList = getxmlelement(xml_root, 'swathTiming/burstList')
        passtype=getxmlvalue(xml_root, 'generalAnnotation/productInformation/pass')
        orbitNumber = int(getxmlvalue(xml_root, 'adsHeader/absoluteOrbitNumber'))
        # relative orbit number
        # link: https://forum.step.esa.int/t/sentinel-1-relative-orbit-from-filename/7042/20
        if os.path.basename(zipname).lower().startswith('s1a'):
            trackNumber = (orbitNumber - 73) % 175 + 1
        else:
            trackNumber = (orbitNumber - 27) % 175 + 1
        lineperburst = int(getxmlvalue(xml_root, 'swathTiming/linesPerBurst'))
        geocords, tiff_path = self.getCoordinates(zipname)
        for index, burst in enumerate(list(burstList)):
            sensingStart = burst.find('azimuthTime').text
            dt = read_time(sensingStart)-read_time(ascNodeTime)
            time_info = int((dt.seconds + dt.microseconds*1e6)/burst_interval)
            burstID = "t"+str(trackNumber) + "s" + self.swath + "b" + str(time_info)
            thisBurstCoords, xc, yc = self.burstCoords(geocords, lineperburst, index)
            # check if self.df has this dt for this track. If not append it
            
            burst_query = self.df.query("burst_ID=='{}'".format(burstID))
            if burst_query.empty:
                print("adding {} to the dataframe".format(burstID))
             
                self.df = self.df.append({'burst_ID':burstID,
                                          'pass_direction':passtype,
                                          'longitude':xc,
                                          'latitude':yc,
                                          'geometry':thisBurstCoords.wkt
                                          }, ignore_index=True)

            else:
                print('The Unique ID {} already exists.'.format(burstID))

 
            self.df_tseries = self.df_tseries.append({'burst_ID': burstID,
                                                      'date': read_time(sensingStart).strftime("%Y-%m-%d"),
                                                      'url': self.url,
                                                      'measurement': tiff_path,
                                                      'annotation': annotation_path,
                                                      'start':index*lineperburst,
                                                      'end':(index+1)*lineperburst},
                                                       ignore_index=True)

        zf.close()    


    def to_csv(self, output_id, output_id_tseries):
        """
        The function to store the data frames to CSV files
        Parameters:
            output_id: name of the output file for the Burst ID data frame
            output_id_tseries: name of the output file for the time-series of the bursts
        """

        self.df.to_csv(output_id, mode='w', index=False)
        self.df_tseries.to_csv(output_id_tseries, mode='w', index=False)

    def upload_to_s3(self, filename, bucket_name):
        """
        The function to upload a file to S3
        Parameters:
            filename: the path of the file to be uploaded
            bucket_name: the name of the bucket on S3
        """

        fileObj = s3UploadDownload(bucket_name)
        fileObj.put_file(filename)


def getxmlattr( xml_root, path, key):
    """
    Function to extract the attribute of an xml key
    """

    try:
        res = xml_root.find(path).attrib[key]
    except:
        raise Exception('Cannot find attribute %s at %s'%(key, path))

    return res

def getxmlvalue( xml_root, path):
    """
    Function to extract value in the xml for a given path
    """

    try:
        res = xml_root.find(path).text
    except:
        raise Exception('Tag= %s not found'%(path))

    if res is None:
        raise Exception('Tag = %s not found'%(path))

    return res

def getxmlelement(xml_root,  path):
    """
    extract an element of a xml file
    """

    try:
        res = xml_root.find(path)
    except:
        raise Exception('Cannot find path %s'%(path))

    if res is None:
        raise Exception('Cannot find path %s'%(path))

    return res


def read_time(input_str, fmt="%Y-%m-%dT%H:%M:%S.%f"):
    """
    The function to convert a string to a datetime object
    Parameters:
        input_str: A string which contains the data time with the format of fmt
        fmt: the format of input_str

    Returns:
        dt: python's datetime object
    """

    dt = datetime.datetime.strptime(input_str, fmt)
    return dt

