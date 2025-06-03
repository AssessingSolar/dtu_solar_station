
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

print(pd.Series(missing_dates).dt.strftime('%Y-%m').value_counts())

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

# %%

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


# %% Plot all columns

for c in df_qc.columns:
    if c == 'Solys_gps_time':
        continue
    plt.figure()
    df_qc.loc[df.index.year == 2015, c].plot()
    plt.title(c)
    plt.show()

# %%
year = 2015

parameters = ['GHI', 'DHI', 'DNI']

df_qc.loc[df_qc.index.year==year, parameters].plot(ylim=(-10,1200), subplots=True, sharex=True)
#df_qc.loc['2018-01-01':, parameters].plot(ylim=(-200,600), subplots=True, sharex=True)


# %% BSRN checks of main measurements

erl_dhi = pvanalytics.quality.irradiance.check_dhi_limits_qcrad(
    dhi=df_qc['sun_diffuse'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='extreme')
ppl_dhi = pvanalytics.quality.irradiance.check_dhi_limits_qcrad(
    dhi=df_qc['sun_diffuse'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='physical')

erl_ghi = pvanalytics.quality.irradiance.check_ghi_limits_qcrad(
    ghi=df_qc['sun_total'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='extreme')

ppl_spn1_ghi = pvanalytics.quality.irradiance.check_ghi_limits_qcrad(
    ghi=df_qc['sun_total'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='physical')


# %%
ghi_ppl, dhi_ppl, dni_ppl = pvanalytics.quality.irradiance.check_irradiance_limits_qcrad(
        solar_zenith=solpos['apparent_zenith'],
        dni_extra=df_qc['dni_extra'],
        ghi=df_qc['GHI'],
        dhi=df_qc['DHI'],
        dni=df_qc['DNI'],
        limits='extreme',
)

# %%

df_sub = df_qc['2021-09-25 00:00': '2021-10-20 00:00']
df_sub = df_qc['2021-09-25 00:00': '2021-10-06 00:00']
df_sub = df_qc['2021-10-04 00:00': '2021-10-06 00:00']
axes = df_sub[['GHI','DHI','DNI']].plot(subplots=True, sharex=True)



plot_measured_vs_calculated_ghi(df_sub['GHI'], df_sub['DHI'], df_sub['DNI'],
                                solpos.loc[df_sub.index, 'apparent_zenith'], s=1, alpha=0.5)
# _ = plot_diffuse_fraction_vs_clearness_index(
#     ghi=df_sub['GHI'], dhi=df_sub['DHI'], solar_zenith=solpos.loc[df_sub.index, 'apparent_zenith'],
#     dni_extra=df_sub['dni_extra'], mask=df_sub['GHI']>50, s=0.5, alpha=0.2, xlim=(None, None), ylim=(None, None))

# %%


# %%

def plot_diffuse_fraction_vs_clearness_index(ghi, dhi, solar_zenith, dni_extra, mask=None,
                                             c=None, xlim=(0, 2), ylim=(0, 1.5), **kwargs):
    mask = np.ones(len(ghi)).astype(bool) if mask is None else mask
    c = c if c is None else c[mask]

    fig, ax = plt.subplots()
    plt.scatter(
        x = ghi[mask] / (dni_extra[mask] * np.cos(np.deg2rad(solar_zenith[mask])).clip(lower=0)),
        y = dhi[mask] / ghi[mask],
        c=c, **kwargs)

    ax.set_xlabel('Diffuse fraction (DHI/GHI) [-]')
    ax.set_ylabel('Clearness index (GHI/ETH) [-]')
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    plt.show()
    return fig, ax


def plot_measured_vs_calculated_ghi(ghi, dhi, dni, solar_zenith, mask=None, c=None,
                                    xlim=(-10, 1200), ylim=(-10, 1200), **kwargs):
    mask = np.ones(len(ghi)).astype(bool) if mask is None else mask
    c = c if c is None else c[mask]

    fig, ax = plt.subplots()
    plt.scatter(
        x = ghi[mask],
        y = dhi[mask].clip(lower=0) + \
            (dni[mask] * np.cos(np.deg2rad(solar_zenith[mask])).clip(lower=0)).clip(lower=0),
        c=c, **kwargs)

    ax.set_xlabel('Measured GHI [W/m$^2$]')
    ax.set_ylabel('Calculated GHI [W/m$^2$]')
    ax.plot([0, 1200], [0, 1200], c='r', alpha=0.8)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    plt.show()
    return fig, ax

_ = plot_diffuse_fraction_vs_clearness_index(
    ghi=df_qc['GHI'], dhi=df_qc['DHI'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], mask=df_qc['GHI']>50, s=0.5, alpha=0.2)

# %% SPN1 check

dfp = df_qc[df_qc['sun_total'] > 50]

fig, ax = plt.subplots()
plt.scatter(
    x=dfp['sun_total'] / dfp['ghi_extra'],
    y=dfp['sun_diffuse'] / dfp['sun_total'],
    c=solpos.loc[dfp.index, 'apparent_elevation'],
    s=0.5, alpha=0.2)

ax.set_xlabel('sun_total / ghi_extra')
ax.set_ylabel('sun_diffuse / sun_total')
# ax.set_xlim(0, 2)
# ax.set_ylim(-0.1, 1.2)

# %% SPN1 BSRN checks
consistent_components_spn1, diffuse_ratio_limit_spn1 = \
    pvanalytics.quality.irradiance.check_irradiance_consistency_qcrad(
        solar_zenith=solpos['apparent_zenith'],
        ghi=df_qc['sun_total'],
        dhi=df_qc['sun_diffuse'],
        dni=np.nan,
        outside_domain=True)

erl_spn1_dhi = pvanalytics.quality.irradiance.check_dhi_limits_qcrad(
    dhi=df_qc['sun_diffuse'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='extreme')
ppl_spn1_dhi = pvanalytics.quality.irradiance.check_dhi_limits_qcrad(
    dhi=df_qc['sun_diffuse'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='physical')

erl_spn1_ghi = pvanalytics.quality.irradiance.check_ghi_limits_qcrad(
    ghi=df_qc['sun_total'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='extreme')

ppl_spn1_ghi = pvanalytics.quality.irradiance.check_ghi_limits_qcrad(
    ghi=df_qc['sun_total'], solar_zenith=solpos['apparent_zenith'],
    dni_extra=df_qc['dni_extra'], limits='physical')

# %%
df_qc.loc['2024-06-17 11:09':'2024-06-17 11:27', 'LWD'].plot(ylim=(-200,600))


# %%


df_qc.loc[(df.index.year==2015), irradiance_cols].plot(
    subplots=True, sharex=True, figsize=(8,8))

# %%
# 2018, 2021 was an ugly year

df_qc[df_qc.index.year==202].plot.scatter(
    x='GHI', y='sun_total', xlim=[-10, 1200], ylim=[-10, 1200],
    s=0.1, alpha=0.4)
plt.plot([0, 1200], [0, 1200], c='r', alpha=0.5)
