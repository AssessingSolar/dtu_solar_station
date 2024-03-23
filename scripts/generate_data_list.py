import pandas as pd
import glob
import os

files = glob.glob('data/*.csv')
file_basenames = [os.path.basename(f) for f in files]

if len(file_basenames) == 0:
    raise ValueError('No data files found.')

month_years = pd.Series(pd.to_datetime(f[-11:-4], format='%Y_%m') for f in files)
years = sorted(set(month_years.dt.year), reverse=True)
months = month_years.dt.strftime('%b').unique()

url = "https://raw.githubusercontent.com/AssessingSolar/dtu_solar_station/main/"

lines = []
for y in years:
    lines.append("")
    lines.append(f"## {y}")
    for m in months:
        month_number = pd.to_datetime(m, format='%b').strftime('%m')
        filename = f"dtu_{y}_{month_number}.csv"
        if filename in file_basenames:
            l = f"- [{m} {y}]({url}data/{filename})"
        lines.append(l)

with open('docs/data.txt', 'w') as f:
    for line in lines:
        f.write(line)
        f.write('\n')

# %%
header = '|   |' + ''.join([f" {m} |" for m in months])

separator = ''.join(['|---']*(len(months)+1)) + '|'

lines = [header, separator]
for y in years:
    line = f"| {y} |"
    for m in months:
        month_number = pd.to_datetime(m, format='%b').strftime('%m')
        filename = f"dtu_{y}_{month_number}.csv"
        if filename in file_basenames:
            text = f"{m} {y}"
            link = os.path.join([url, filename])
            line += f" [{text}]({link}) |"
        else:
            line += "        "
    lines.append(line)

lines.append(separator)

# %%
    year_files = sorted(glob.glob(f'data/dtu_{y}*.csv'))
    
    for f in year_files:
        m = year_files
        link = os.path.join([url, f])
        text = 
        
    

    
    month_number = pd.to_datetime('Feb', format='%b').strftime('%m')
    filename = f"dtu_{y}_{month_number}.csv"


    line = f'| {y} |' + ''.join([f' [link]({m}) |' for m in months])
    lines.append(line)
