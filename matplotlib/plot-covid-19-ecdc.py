#!/usr/bin/python3

import argparse
import datetime
import math
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
import sys

# Globals

countries = ['US', 'DE', 'IT', 'FR', 'ES', 'CH', 'HU', 'IN', 'UK', 'IS',  'JP',
                         'AT', 'SE']
countries = ['FR', 'ES', 'IT', 'DE', 'US', 'AT', 'CN', 'KR', 'JP']
countries = ['US', 'DE', 'IT', 'FR', 'ES', 'CN', 'KR', 'JP']


# Plots the growth in COVID-19 cases or deaths from the day each country
# reached 100 cases or 10 deaths, respectively.

# The ECDC data is in Excel format, requiring Pandas or something else that can
# read that form
# To avoid downloading the data for every run, run this once per day and then
# pass the local file name on the command line, e.g.:
# wget https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-2020-03-22.xlsx
# python plot-covid-19-ecdc.py COVID-19-geographic-disbtribution-worldwide-2020-03-22.xlsx

ap = argparse.ArgumentParser()
ap.add_argument('path', type=str, nargs='?', help='path to Excel file')
ap.add_argument('-d', '--deaths', action='store_true', help='plot deaths')
ap.add_argument('-n', '--normalize', action='store_true',
                help='normalize to 1 million population')
ap.add_argument('-s', '--start', metavar='S', type=float, help='start at S')
ap.add_argument('-t', '--timestamp', action='store_true',
                help='add timestamp to file name')
args = ap.parse_args()

def url_for_date(date):
    return 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + date.isoformat() + '.xlsx'


normalize = args.normalize
timestamp = args.timestamp
report_cases = not args.deaths
date = datetime.date.today()
path = args.path or url_for_date(date)

# Handle case where data for today is not available yet, try to use data
# from yesterday
try:
    df = pd.read_excel(path)
except FileNotFoundError:
    if args.path:
        raise
    print(path + ' not found.')
    date -= datetime.timedelta(days=1)
    path = url_for_date(date)
    print('Trying: ' + path)
    df = pd.read_excel(path)

# Format change on 2020-03-27
if 'geoId' in df.keys():
    columns = ['geoId', 'dateRep', 'cases' if report_cases else 'deaths',
               'popData2018']
else:
    columns = ['GeoId', 'DateRep', 'Cases' if report_cases else 'Deaths']
    # No population data available
    normalize = False

min_y = args.start or (100 if report_cases else 10) * (0.02 if normalize else 1)

country_dict = {}
# Group by 'GeoId' and not "Countries and territories" because the latter has
# inconsistent capitalization ('CANADA' and 'Canada').
for country, group in df.groupby(columns[0]):
    if country in countries:
        # Reverse the time order for each group
        df2 = group.iloc[::-1][columns]
        value = (df2[columns[2]].cumsum() *
                 (1e6 / df2[columns[3]] if normalize else 1))
        df2['cum'] = value
        df2 = df2.loc[df2['cum'] >= min_y]
        if len(df2) > 1:
            country_dict[country] = df2[[columns[1], 'cum']]
        else:
            print('Country', country, 'has too low a value, ignored.')

# Limit to 5 days past the second longest (for China)
counts = np.array([len(country_dict[c]) for c in country_dict])
counts.partition(len(counts) - 1)
max_x = min(counts[-2] + 5, counts[-1])
max_y = max(country_dict[c].iloc[-1]['cum'] for c in country_dict)

fig, ax = plt.subplots()
plt.yscale('log')
plt.grid()
ax.yaxis.set_major_locator(LogLocator(subs=(1, 2, 5)))
# Don't use scientific notation for the y-axis and add thousand separators
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda x, _: ('{:,.0f}' if x >= 1 else '{:.1f}').format(x)))

# Draw dotted lines indicating doubling in 1-7 days.
for d in range(1, 8):
    x2 = math.log(max_y / min_y) / math.log(pow(2, 1 / d))
    y2 = max_y
    if x2 > max_x - 1:
        x2 = max_x - 1
        y2 = pow(pow(2, 1 / d), x2) * min_y
    ax.add_line(mlines.Line2D([0, x2], [min_y, y2], c='#666',
                              ls='dotted', lw=0.75))

# Plot the selected countries and print the total for each country.
for country in countries:
    # Some countries might not have more than 1 data point
    if country in country_dict:
        df2 = country_dict[country]
        c = min(max_x, len(df2))
        ax.plot(range(c), df2['cum'][:c],
                label=country, lw=0.75, marker='.', ms=4)
        print(country, df2.iloc[-1]['cum'])

# change window and default file name to something else than figure 1:
f = plt.gcf()
window_title = 'covid-19-{0}-ecdc{1}{2}'.format(
    'cases' if report_cases else 'deaths',
    '-normalized' if normalize else '',
    '-' + str(date) if timestamp else '')
f.canvas.set_window_title(window_title)

chart_title = 'Coronavirus Total {0}{1}'.format(
    'Cases' if report_cases else 'Deaths',
    ' Normalized (per Mio. Population)' if normalize else '')
chart_source = 'Source: ' + path
plt.title(chart_title)
font = FontProperties()
font.set_size('x-small')
plt.figtext(0.99, 0.01, chart_source, fontproperties=font,
            horizontalalignment='right')
ax.legend(loc='lower right')
plt.xlim(left=0)
plt.ylim(bottom=min_y)
plt.show()
