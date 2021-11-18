#!/usr/bin/env python3
import json
import os
import glob
import datetime
import argparse

from query import query_asf, read_query
from BurstDataFrame import BurstDataFrame 


EXAMPLE = """example:
  create_burst_id.py                         #run with showing help'
  create_burst_id.py -h / --help             #help
  create_burst_id.py -H                      #print default options
  create_burst_id.py -b 10 11 -121 -120     #runs with the given bounding box. Queries the archive for the Sentinel-1 data over the region of interest
  create_burst_id.py -d /scratch/fattahi/s1_data # Ignores the bounding box and ignores searching the archive. Instead searches the input directory for the Sentinel-1 zip files (looking for the pattern of S1*IW*SLC*zip)
"""

def create_parser():
    parser = argparse.ArgumentParser(description='Sample script to create burst id database',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument('-d', '--frame_dir', type = str, default = None, dest = 'frame_dir', help = 'The directory with existing Sentiel-1 SLC zip file.')
    parser.add_argument('-b', '--bbox', type = float, default = None, nargs = '+', dest = 'bbox', help = 'Defines the spatial bounding box in the format south north west east.')
    parser.add_argument('-s', '--start_date', type = str, default = '2019-01-01', dest = 'start_date', help = 'Start date to search the asf archive. Format: YYYY-MM-DD. Default: 2019-01-01')
    parser.add_argument('-e', '--end_date', type = str, default = '2019-02-01', dest = 'end_date', help = 'End date to search the asf archive. Format YYYY-MM-DD. Deafult: 2019-02-01')
    parser.add_argument('-p', '--platform', type = str, default = 'Sentinel-1', dest = 'platform', help = 'Name of the Sentinel-1 platform to search (Sentinel-1A, Sentinel-1B, Sentinel-1). Deafult: Sentinel-1 which queries both Sentinel-1A and Sentinel-1B')
    parser.add_argument('-o', '--output_name', type = str, default = 'burstID', dest = 'output_name', help = 'File name of the output burst database. Deafult: burstID-database. This will create two geopandas databases: 1) burstID.csv and 2) burstID_stack.csv. The first one is a geopandas database of unique burst ids and their coordinates on the ground. The second is geopandas database of the stack of slcs with their unique burst ids determined. ')
    return parser

def main():
    """
    main driver to create the databases of the unique burst IDs.
    """

    parser = create_parser()
    args = parser.parse_args()

    if args.frame_dir is None:
        snwe = tuple(args.bbox) 
        output_query_file = "query_asf.json"
        query_asf(output_query_file, snwe, args.start_date, args.end_date, sat=args.platform)
        urls = read_query(output_query_file)    
        print(f'number of frames found: {len(urls)}')
        print(urls)
        frameList = []
        dfObj = BurstDataFrame()
        for url in urls:
            frame = os.path.basename(url)
            if not os.path.exists(frame):
                print(f'downloading {url}')
                cmd = "wget {}".format(url)
                os.system(cmd)
            else:
                print(f'{frame} already exists.')
            frameList.append(frame)
            print(f'update database using {frame}')
            dfObj.url = url
            for swath in range(3):
                dfObj.swath = str(swath+1)
                dfObj.update(frame)
    else:
        frameList = glob.glob(os.path.join(args.frame_dir, "S1*IW*SLC*zip"))
        print(f'Number of files found: {len(frameList)}')
        dfObj = BurstDataFrame()
        for frame in frameList:
            print(f'update database using {frame}')
            dfObj.url = frame
            for swath in range(3):
                dfObj.swath = str(swath+1)
                dfObj.update(frame)
    
    output_burst_ids = args.output_name + ".csv"
    output_burst_ids_stack = args.output_name + "-stack.csv"
    dfObj.to_csv(output_burst_ids, output_burst_ids_stack)

if __name__ == '__main__':
    main()

