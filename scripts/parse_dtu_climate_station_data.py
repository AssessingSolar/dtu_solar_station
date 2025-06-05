
import glob
import pandas as pd
import pvlib
import pvanalytics
import os
import numpy as np
import warnings
import matplotlib.pyplot as plt

data_path = 'C:/Users/arajen/OneDrive - Danmarks Tekniske Universitet/Skrivebord/Climate station data/'

# %% To do
# When were the partly shaded pyranometers taken down? Make a list
# What is LWD really? Is it the upwelling or?

# %%

parameter_dict = {
    'Mod2Ch1': 'LWD',
    'Mod2Ch2': 'DHI_shadow_band',
    'Mod2Ch3': 'DHI',
    'Mod2Ch5': 'DNI',
    'Mod2Ch6': 'GHI',
    'Mod2Ch7': 'GTI_270_90',
    'Mod2Ch8': 'GTI_0_90',
    'Mod2Ch9': 'GTI_90_90',
    'Mod2Ch10': 'GTI_180_90',
    'Mod2Ch11': 'GTI_180_45',
    'RTD0_Pyrheliometer': 'DNI_temperature',
    'RTD2': 'LWD_temperature',
}

weather_parameters = [
    'wind_dir_min', 'wind_dir_avg', 'wind_dir_max',
    'wind_speed_min', 'wind_speed_avg', 'wind_speed_max',
    'air_temperature', 'relative_humidity', 'air_pressure',
    'rain_accumulation', 'rain_duration', 'rain_intensity',
    'hail_accumulation', 'hail_duration', 'hail_intensity',
]


precipitation_parameters = [
    'rain_duration', 'rain_intensity', 'rain_accumulation',
    'hail_accumulation', 'hail_duration', 'hail_intensity',
]

channels_not_in_use = [
    'Mod2Ch4',  # Not in use according to report
    'Mod3Ch1', 'Mod3Ch2', 'Mod3Ch3', 'Mod3Ch4', 'Mod3Ch5', 'Mod3Ch6', 'Mod3Ch7', 'Mod3Ch8',
    'Mod3Ch9', 'Mod3Ch10', 'Mod3Ch11', 'Mod3Ch12', 'Mod3Ch13', 'Mod3Ch14', 'Mod3Ch15', 'Mod3Ch16',
    'Mod2Ch12', 'Mod2Ch13', 'Mod2Ch14', 'Mod2Ch15', 'Mod2Ch16',
]

half_dome_sensors = [f"Mod1Ch{i}" for i in range(1, 17)]

irradiance_cols = ['GHI', 'DHI', 'DNI', 'sun_diffuse', 'sun_total']

gti_columns = ['GTI_270_90', 'GTI_0_90', 'GTI_90_90', 'GTI_180_90', 'GTI_180_45']

# %% Timestamp parsing


def date_parser(date_str):
    """Parse timestamps in mixed formats."""
    if isinstance(date_str, (int, float)):
        return pd.NaT
    if date_str[2] == '-':  # e.g., 04-01-2014 23:59
        format = '%m-%d-%Y %H:%M'
    elif date_str[2] == ':':  # e.g., 00:00:01 08/26/2014
        format = '%H:%M:%S %m/%d/%Y'
    else:
        raise UserWarning(f"Timestamp {date_str} does not match any format")
    return pd.to_datetime(date_str, format=format)


# %% Sort filenames according to date

def get_file_date(filename):
    return pd.to_datetime(filename[-12:-4], format='%m-%d-%y')


filenames = glob.glob(data_path + '*')
filenames = [f for f in filenames if get_file_date(f).year != 2014]
file_dates = sorted([get_file_date(f) for f in filenames])
filenames = sorted(filenames, key=lambda s: file_dates.index(get_file_date(s)))

complete_dates = pd.date_range(min(file_dates), max(file_dates), freq='1d')
missing_dates = sorted(set(complete_dates).difference(file_dates))

print("Missing days\n", pd.Series(missing_dates).dt.strftime('%Y-%m').value_counts())

# %% Read in data
dfs = []
for f in filenames:
    basename = os.path.basename(f)
    file_date = get_file_date(f)
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")

        dfi = pd.read_csv(f, sep='\t', skip_blank_lines=True,
                          on_bad_lines='warn', na_values=[-9999])

        dfi['file_date'] = file_date

        if len(w) == 1:  # pd.read_csv engine choice specific
            warning_messages = str(w[0].message).strip().split('\n')
            warning_lines = [int(warning_messages[0].split()[2].strip(':'))
                             for m in warning_messages]
            print(f"{basename.rstrip('.txt')}  Warning lines: {len(warning_lines)}")
        if len(w) > 1:
            raise ValueError("Multiple warning types")

    dfs.append(dfi)

# %%
df = pd.concat(dfs, axis=0)
df['Time(utc)'] = df['Time(utc)'].apply(lambda s: date_parser(s))
df = df.set_index('Time(utc)')
df = df[df.index.notna()]
df = df.rename(columns=parameter_dict)
df.index = df.index.round('min')
# drop 2 instances of duplicated indexes (due to rounding)
df = df[~df.index.duplicated()]
# remove few incorrect time stamps (7 instances found in 2015 files)
df = df[df.index != '1904-01-01']
# Ensure consistent frequency (add missing timestamps)
df = df.asfreq('1min')


# Note from Elsa's logbook:
# 11-5-2018: P1-P16 samt kupler er pillet ned. Dog sidder pyranometeret Mod1Ch7 stadig og måler
# med en helt lukket kuppel.
df.loc['2018-05-11':, half_dome_sensors] = np.nan

# %% Drop unused/unnecessary columns
df = df.drop(columns=channels_not_in_use)
df = df.drop(columns=half_dome_sensors)
df = df.drop(columns=gti_columns)

columns_drop = [
    'wind_dir_min.1',  # only available for part of January 2015
    'Mod1ch16',  # incorrect naming for January 2015
    # SOLYS 2 / sun sensor parameters
    'Q1_Sun_intensity', 'Q2_Sun_intensity', 'Q3_Sun_intensity', 'Q4_Sun_intensity',
    'Solys_instrument_status', 'Total_Sun_intensity', 'Function',
    # Temperature parameters
    'RTD1',  # seems to be just noise
    'RTD3',  # value always stuck at 310.8
    'RTD3_Cabinet',  # values seem to be incorrect
]

df = df.drop(columns=columns_drop)

# %% Alternative NAN values

nan_1290_parameters = ['sun_total', 'sun_diffuse', 'DNI_temperature', 'LWD_temperature']

for p in nan_1290_parameters:
    df[p] = df[p].replace(-1290, np.nan)

# %% Calculate solar position
location = pvlib.location.Location(latitude=55.7906, longitude=12.5251)
solpos = location.get_solarposition(df.index)

df['GHI_calc'] = (
    df['DHI'].clip(lower=0)
    + (df['DNI'] * np.cos(np.deg2rad(solpos['apparent_zenith']))).clip(lower=0))

df['dni_extra'] = pvlib.irradiance.get_extra_radiation(df.index)
df['ghi_extra'] = df['dni_extra'] * (np.cos(np.deg2rad(solpos['apparent_zenith']))).clip(lower=0)

# %% Copy dataframe

df_qc = df.copy()

# %% Apply manual corrections

# Handle offset
# Calculate missing component

qc_path = 'C:/github/dtu_solar_station/metadata/'
qc_filename = 'manual_corrections.csv'


def read_qc_file(filename):
    """Read manual corrections file."""
    qci = pd.read_csv(filename, comment='#')
    qci['start'] = pd.to_datetime(qci['start'], format='mixed')
    qci['end'] = pd.to_datetime(qci['end'], format='mixed')
    return qci


filename = qc_path + qc_filename
qc = read_qc_file(filename)

for _, row in qc.iterrows():
    columns = row['columns'].split(';')
    if ',' in row['columns']:
        raise ValueError(f"Incorrectly formatted 'columns': {row['columns']}")
    if row['start'] > row['end']:
        raise ValueError(f"Start ({row['start']}) cannot be after end ({row['end']})")
    # Apply same action to the pyrheliometer body temperature as the output signal
    columns = columns + ['DNI_temperature'] if 'DNI' in columns else columns
    columns = columns + ['LWD_temperature'] if 'LWD' in columns else columns

    if row['action'] == 'remove':
        df_qc.loc[row['start']: row['end'], columns] = np.nan


# These
df_qc.loc['2018-03-21 00:00': '2018-06-21 16:35', 'DHI'] = 8.34/8.59 * \
    df_qc.loc['2018-03-21 00:00': '2018-06-21 16:35', 'DHI']

df_qc.loc['2015-03-11 00:00': '2015-05-13 17:20', 'GHI'] = 4.98/5.065 * \
    df_qc.loc['2015-03-11 00:00': '2015-05-13 17:20', 'GHI']


# Important to recalculate
df_qc['GHI_calc'] = (
    df_qc['DHI'].clip(lower=0)
    + (df_qc['DNI'] * np.cos(np.deg2rad(solpos['apparent_zenith']))).clip(lower=0))

# df_qc.to_pickle('quality_controlled_dtu_data.pkl')
