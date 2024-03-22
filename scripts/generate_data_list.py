import pandas as pd
import glob
import os

files = glob.glob('data/*.csv')
file_basenames = [os.path.basename(f) for f in files]

month_years = pd.Series(pd.to_datetime(f[-11:-4], format='%Y_%m') for f in files)

months = month_years.dt.strftime('%b').unique()

years = sorted(set(month_years.dt.year), reverse=True)

url = "https://raw.githubusercontent.com/AssessingSolar/dtu_solar_station/main/"

lines = []
for y in years:
    lines.append("")
    lines.append(f"## {y}")
    for m in months:
        month_number = pd.to_datetime('Feb', format='%b').strftime('%m')
        filename = f"dtu_{y}_{month_number}.csv"
        if filename in file_basenames:
            l = f"- [{m} {y}]({url}data/{filename})"
        lines.append(l)

with open('docs/data.txt', 'w') as f:
    for line in lines:
        f.write(line)
        f.write('\n')
