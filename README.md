# sentinel1-burst-id

A prototype for assigning a unique burst id to Sentinel-1 SLC bursts

## Installation

```bash
# download source code
cd ~/tools/
git clone https://github.com/opera-adt/sentinel1-burst-id.git

# install dependencies
conda install --file sentinel1-burst-id/requirements.txt wget
```

Setup environment variables as below:

```bash
export S1_BURST_ID_HOME=~/tools/sentinel1-burst-id
export PYTHONPATH=${PYTHONPATH}:${S1_BURST_ID_HOME}/src
export PATH=${PATH}:${S1_BURST_ID_HOME}/bin
```

## Usage


In order to run a sample script which creates a database of burst ids one can run create_burst_id.py using an already downloaded set of zip files. 

```
create_burst_id.py -d input_dir_with_Sentinel-1_zip_files
```
or the script can search the ASF archive based on the input bounding box:

```
create_burst_id.py -b 30 31 -121 -120

```

There are more arguments that can be setup to run the script such as start date, end date, etc. Run the script with --help for a complete list of options:

```
create_burst_id.py --help

optional arguments:
  -h, --help            show this help message and exit
  -d FRAME_DIR, --frame_dir FRAME_DIR
                        The directory with existing Sentiel-1 SLC zip file.
  -b BBOX [BBOX ...], --bbox BBOX [BBOX ...]
                        Defines the spatial bounding box in the format south north west east.
  -s START_DATE, --start_date START_DATE
                        Start date to search the asf archive. Format: YYYY-MM-DD. Default: 2019-01-01
  -e END_DATE, --end_date END_DATE
                        End date to search the asf archive. Format YYYY-MM-DD. Deafult: 2019-02-01
  -p PLATFORM, --platform PLATFORM
                        Name of the Sentinel-1 platform to search (Sentinel-1A, Sentinel-1B, Sentinel-1). Deafult: Sentinel-1 which queries both Sentinel-1A and Sentinel-1B
  -o OUTPUT_NAME, --output_name OUTPUT_NAME
                        File name of the output burst database. Deafult: burstID-database. This will create two geopandas databases: 1) burstID.csv and 2) burstID_stack.csv. The first one is a geopandas database of unique burst ids and their coordinates on the ground. The second is geopandas database of the stack of slcs with their unique burst ids determined.

```
The output of the script is two geopandas dataframes. The first one (burstID) is a database of unique burst IDs which can be read as:

```
import pandas as pd

df = pd.read_csv("burstID.csv")
df.head()
```

<img width="1189" alt="Screen Shot 2021-11-18 at 1 23 31 PM" src="https://user-images.githubusercontent.com/5033183/142498924-872262e5-1ea9-42d9-ad93-95cf6eeea7f2.png">

In the example above the first column is the defined burst id. The first defined burst id is **t71s1d2398** which should be decoded as

t71 : Track 71
s1: sub-swath 1
d: Descending orbit
2398: time since last ascending node time in seconds. (This value is constant within some fractional seconds. Since the burst duration is around 3 seconds, the rounded integer value remains unique for this track. Together with the track number, swath number and the orbit direction, the ID should be unique (to be confirmed) for agiven date and track and repeats for the next cycle of the observation over the same region and from same track.)
To see a plot of the bursts one can use geopandas as shown below:

```
import pandas as pd
import shapely
import geopandas as gpd
import pyproj


df = pd.read_csv("burstID_database.csv")

df['geometry'] = df['geometry'].apply(shapely.wkt.loads)
gdf = gpd.GeoDataFrame(df, crs='epsg:4326')

gdf.plot()
```

Once the database exists one can easily query and intersect with a bounding box or filter with different metadata.

```
poly = Polygon(zip([-120,-119,-119,-120], [30.0,30,31,31]))
x,y = poly.exterior.xy

fig,ax =plt.subplots(1,figsize=(20,10))
gdf.plot(color='blue', ax=ax)
gdf[gdf.intersects(poly)].plot(figsize=(30,20), color='lime',ax=ax)
ax.plot(x,y, linewidth=10)
```


<img width="486" alt="Screen Shot 2021-11-19 at 9 38 51 AM" src="https://user-images.githubusercontent.com/5033183/142666980-430fdff3-cdcf-4491-9763-6fab957b3e89.png">


The second output database is burstID-stack.csv which represents the database of the stack of Sentinel-1 frames with bursts labeled and the metdata to extract each burst is defined. 

```
import pandas as pd

df = pd.read_csv("burstID-stack.csv")
df.head()
```


# License
**Copyright (c) 2021** California Institute of Technology (“Caltech”). U.S. Government
sponsorship acknowledged.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
* Redistributions of source code must retain the above copyright notice, this list of conditions and
the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the
distribution.
* Neither the name of Caltech nor its operating division, the Jet Propulsion Laboratory, nor the
names of its contributors may be used to endorse or promote products derived from this software
without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

