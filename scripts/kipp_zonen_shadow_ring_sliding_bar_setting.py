"""Script for generating slide bar settings for Kipp & Zonen shadow ring."""

import numpy as np
import pandas as pd
import pvlib

# Information has been taken from the Kipp & Zonen CM 121 shadow ring
# instruction manual.

# Note that the correction factors are based on the assumption of a horizontal
# pyranometer installation and uniform diffuse sky irradiance.

# The sliding bar has two scales; a higher and a lower one. At
# positive solar declinations (between 21 Mar. and 23 Sep.) the part of the
# scale that is oriented south must be read. In the northern hemisphere this is
# the lower part.

# The sliding bar adjustment can be derived with the formula
# L = abs(297 tan (D)), in which D is the declination of the sun.


def calculate_sliding_bar_setting(declination):
    """
    Determine Kipp & Zonen shadow ring sliding bar setting.

    Parameters
    ----------
    declination : numeric
        Declination angle [degrees].

    Returns
    -------
    numeric
        Sliding bar setting [cm].

    """
    sliding_bar_mm = 297 * np.tan(np.deg2rad(np.abs(declination)))
    sliding_bar_cm = np.round(sliding_bar_mm / 10, 1)
    return sliding_bar_cm


times = pd.date_range(start='2025-01-01', end='2025-12-31', freq='1d')

declination = \
    np.rad2deg(pvlib.solarposition.declination_spencer71(times.dayofyear))

slide_bar = calculate_sliding_bar_setting(declination)

df = pd.DataFrame(
    data={
        'Slide bar setting': slide_bar,
        },
    index=[times.strftime('%m %b'), times.day]
    )

df = df.unstack(0)['Slide bar setting']

df = df.fillna('')

df.columns = [c.split(' ')[-1] for c in df.columns]

df.to_excel('../metadata/kipp_zonen_shadow_ring_slide_bar_setting.xlsx')
