import os
from distutils.core import setup

__version__ = version = VERSION = '0.1'

directory = os.path.abspath(os.path.dirname(__file__))

long_description = 'A prototype for labeling Sentinel-1 bursts'

package_data_dict = {}

#package_data_dict[''] = [
#    os.path.join('defaults', 'dswx_hls.yaml'),
#    os.path.join('schemas', 'dswx_hls.yaml')]

setup(
    name='sentinel1-burst-id',
    version=version,
    description='Assign a unique burst id to Sentinel-1 bursts',
    package_dir={'sentinel1-burst-id': '.'},
    packages=['sentinel1-burst-id',
              'sentinel1-burst-id.src',
              'sentinel1-burst-id.scripts'],
    package_data=package_data_dict,
    classifiers=['Programming Language :: Python', ],
    scripts=['scripts/create_burst_id.py'],
    #install_requires=['argparse', 'numpy', 'yamale', 'ruamel',
    #                  'osgeo', 'scipy'],
    # 'tempfile' 'os' 'sys' 'glob' 'mimetypes'
    url='https://github.com/opera-adt/sentinel1-burst-id',
    license='Copyright by the California Institute of Technology.'
    ' ALL RIGHTS RESERVED.',
    long_description=long_description,
)
