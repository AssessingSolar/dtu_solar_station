# Data

Data is freely available in monthly files and can be downloaded from the table below.

````{include} data.txt
````

## Parameters
The data files contain the following parameters with a one-minute frequency:

| Tag name          | Parameter                          | Unit          |
| ----------------- | ---------------------------------- | ------------- |
| Time(utc)         | Time of measurement in UTC         |               |
| GHI               | Global Horizontal Irradiance       | {math}`W/m^2` |
| DNI               | Direct Normal Irradiance           | {math}`W/m^2` |
| DHI               | Diffuse Horizontal Irradiance      | {math}`W/m^2` |
| LWD               | Longwave Downwelling Irradiance    | {math}`W/m^2` |
| wind_speed_avg    | Wind speed                         | {math}`m/s`   |
| wind_dir_avg      | Wind direction                     | degrees       |
| air_temperature   | Ambient air temperature            | °C            |
| air_pressure      | Air pressure                       | hPa           |
| relative_humidity | Relative humidity                  | %             |
| rain_accumulation | Rain accumulation since last reset | mm            | 
| rain_duration     | Rain duration in 10-s increments   | s             |
| rain_intensity    | Rain intensity (1-min average)     | mm/h          |
