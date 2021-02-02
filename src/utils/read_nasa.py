# Author: Branden Ciranni <branden.ciranni@gmail.com>
# License: MIT License
# Last Updated: 2020-02-02

'''
Module for loading NASA Li-ion Battery Data Set.
Dataset provided by the Prognostics CoE at NASA Ames.

This data can be found at:

- https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/

Functions:

- `_datevec2datetime()`: convert MATLAB datevecs to DateTime Objects
- `_get_metadata()`: get `types`, `start_times`, and `ambient_temps` for all cycles
- `_get_metadata_at()`: get `type`, `start_time`, and `ambient_temp` for a specific cycle
- `_cycle2df()`: convert raw cycle data to pandas DataFrame
- `read_battery()`: read `.mat` file for a given battery number and output pandas DataFrame

Private functions are not meant to be called outside of this Module.

How To Use This Module
======================

```
    import pandas as pd
    from read_nasa import read_battery

    data = read_battery(5)    
```

'''

# load .mat files
from scipy.io import loadmat

# convert MATLAB datevec format to datetime
from datetime import datetime

# store final output in pandas dataframe
from pandas import DataFrame, concat


# Fields measured for each operation
DATA_FIELDS = {
    'charge': [
        'Voltage_measured', 'Current_measured', 'Temperature_measured',
        'Current_charge', 'Voltage_charge', 'Time'
    ],
    'discharge': [
        'Voltage_measured', 'Current_measured', 'Temperature_measured',
        'Current_charge', 'Voltage_charge', 'Time', 'Capacity'
    ],
    'impedance': [
        'Sense_current', 'Battery_current', 'Current_ratio',
        'Battery_impedance', 'Rectified_impedance', 'Re', 'Rct' 
    ]
}    


def _datevec2datetime(vec):
    '''Convert MATLAB datevecs to Python DateTime Objects

    MATLAB datevec example: 
    `[2008.   ,    5.   ,   22.   ,   21.   ,   48.   ,   39.015]`

    Parameters:
    - `vec`: list-like object in MATLAB datevec format
    '''
    return datetime(
        year=int(vec[0]),
        month=int(vec[1]),
        day=int(vec[2]),
        hour=int(vec[3]),
        minute=int(vec[4]),
        second=int(vec[5]),
        microsecond=int((vec[5]-int(vec[5]))*1000)
    )


def _get_metadata(cycles):
    '''Get types, start_times, and ambient_temps for all cycles

    Parameters:
    - `cycles`: nested array-like structure in given format
    '''
    meta = dict()

    # data stored in nested arrays...
    meta['types'] = [arr[0] for arr in cycles['type'][0]]

    # data stored in nested arrays...
    # times in matlab datevec format
    meta['start_times'] = [_datevec2datetime(arr[0]) for arr in cycles['time'][0]]

    # data stored in nested arrays...
    meta['ambient_temps'] = [arr[0][0] for arr in cycles['ambient_temperature'][0]]

    return meta


def _get_metadata_at(meta, i):
    '''Get type, start_time, and ambient_temp for a specific cycle

    Parameters:
    - `meta`: metadata dictionary from `_get_metadata`
    - `i`: cycle index, i.e. the ith cycle
    '''
    return (
        meta['types'][i], 
        meta['start_times'][i], 
        meta['ambient_temps'][i]
    )


def _cycle2df(cycle_data, meta, i):
    '''Convert raw cycle data to pandas dataframe

    Parameters:
    - `cycle_data`: raw cycle data - nested array containing data for all fields 
                    relevant for the cycle, according to the cycle type.
    - `meta`: metadata from `_get_metadata`
    - `i`: cycle index, i.e. the ith cycle
    '''
    dtype, start_time, ambient_temp = _get_metadata_at(meta, i)
    fields = DATA_FIELDS[dtype]

    # create data dict, looks like { field:array_like_data_for_field, ... }
    cycle_dict = {field:cycle_data[0][0][j][0] for j,field in enumerate(fields)}

    # If the data provided is just a single constant element ...
    for col, data in cycle_dict.items():
        if len(data) == 1:
            cycle_dict[col] = data[0]

    # Create DataFrame
    df = DataFrame(cycle_dict)

    # Set Metadata information for cycle
    df['type'] = dtype
    df['start_time'] = start_time
    df['ambient_temp'] = ambient_temp

    return df


def read_nasa(i):
    '''Read `.mat` file for battery i. Constructs the battery name, loads
    the mat file, parses the structure, and uses the above methods to transform
    raw cycle data into pandas DataFrame.

    Parameters:
    - `i`: battery index, corresponding to a battery file, i.e. 5 corresponds to B0005
    '''
    battery_name = 'B00' + '%02d' % i
    file_path = f'./data/raw/{battery_name}.mat'
    mat_contents = loadmat(file_path)

    # for more information on the top level structure, see `./data/raw/README.txt`
    top_level = mat_contents[battery_name]
    cycles = top_level[0,0]['cycle']

    meta = _get_metadata(cycles)
    cycles_data = cycles['data']

    # get a DataFrame for each cycle, and concatenate into one large DataFrame
    df = concat(
        [DataFrame(_cycle2df(cycles_data[0,i], meta, i)) for i in range(len(cycles_data[0]))], 
        ignore_index=True,
        sort=False
    )
    
    return df


if __name__ == '__main__':
    df = read_nasa(5)
    df.to_csv('./data/processed/B0005.csv', index=False)




