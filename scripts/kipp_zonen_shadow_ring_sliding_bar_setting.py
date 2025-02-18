"""Script for generating slide bar settings for Kipp & Zonen shadow ring."""

import numpy as np
import pandas as pd
import pvlib

# Note. That the correction factors are based on the assumption horizontal
# pyranometer installation and on uniform diffuse sky irradiance.

# Note. That the sliding bar has two scales; a higher and alower one. At
# positive solar declinations (between 21 march and 23 sept) the part of the
# scale that is oriented south must be read. In the northern hemisphere this is
# the lower part.

times = pd.date_range(start='2025-01-01', end='2025-12-31', freq='1d')

declination_setting = np.arange(-24, 24+2, 2)

slide_bar_setting = np.array([
    132, 120, 108, 97, 85, 74, 63, 52, 42, 31, 21, 10, 0, 10, 21, 31, 42, 52,
    63, 74, 85, 97, 108, 120, 132])

declination = \
    np.rad2deg(pvlib.solarposition.declination_spencer71(times.dayofyear))

slide_bar = np.interp(declination, declination_setting, slide_bar_setting)

df = pd.DataFrame(
    data={
        'Slide bar setting': slide_bar.round(1),
        },
    index=[times.strftime('%m %b'), times.day]
    )

df = df.unstack(0)['Slide bar setting']

df = df.fillna('')

df.columns = [c.split(' ')[-1] for c in df.columns]

df.to_excel('../metadata/kipp_zonen_shadow_ring_slide_bar_setting.xlsx')
