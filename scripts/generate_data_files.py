"""Code for generating data files. Relies on external script."""
import pandas as pd
latitude_deg_dtu = 55.790697
longitude_deg_dtu = 12.525087
elevation_dtu = 85

start_date = pd.Timestamp('2024-09-01')
end_date = pd.Timestamp.today().round('1d')

df_import = load_weather_data(file_path_raw_weather, start_date, end_date)
df_raw = df_import.copy()
df_raw = rename_data(df_raw)
df_raw = temperature_correction(df_raw)
df_raw = manual_corrections(df_raw)
df_raw =  calculate_solar_values(df_raw, latitude_deg_dtu, longitude_deg_dtu)
df_raw = other_corrections(df_raw)

# %%
rains = ['rain_accumulation', 'rain_duration', 'rain_intensity']
parameters = ['GHI', 'DNI', 'DHI', 'LWD', 'wind_speed_avg', 'wind_dir_avg',
              'air_temperature', 'air_pressure', 'relative_humidity']

months = pd.date_range(start=df_raw.index[0], end=df_raw.index[-1], freq='MS')

for m in months:
    m_end = m + pd.offsets.MonthEnd() + pd.Timedelta(minutes=24*60-1)
    df_sub = df_raw.loc[m: m_end, parameters+rains].asfreq('1min')
    df_sub = df_sub.round(3)
    df_sub.to_csv(f"data/dtu_{m.strftime('%Y_%m')}.csv")
