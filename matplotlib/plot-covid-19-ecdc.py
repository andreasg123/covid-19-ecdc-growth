#!/usr/bin/python3

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

population = {
   'SE': 10099265,
   'AT': 9006398,
   'US': 331002651,
   'DE': 83783942, 
   'IT': 60461826, 
   'FR': 65273511, 
   'ES': 46754778, 
   'CN': 1439323776, 
   'KR': 51269185, 
   'JP': 126476461,
   'CH': 8654622,
   'TK': 84339067,
   'HU': 9660351,
   'IN': 1380004385,
   'IS': 341243,
   'UK': 67886011
}

countries = ['US', 'DE', 'IT', 'FR', 'ES', 'CN', 'KR', 'JP']
countries = ['US', 'DE', 'IT', 'FR', 'ES', 'CH', 'HU', 'IN', 'UK', 'IS', 'CN', 'KR', 'JP', 'AT', 'SE']

# Plots the growth in COVID-19 cases or deaths from the day each country
# reached 100 cases or 10 deaths, respectively.

# The ECDC data is in Excel format, requiring Pandas or something else that can
# read that format.

# To avoid downloading the data for every run, run this once per day and then
# pass the local file name on the command line, e.g.:
# wget https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-2020-03-22.xlsx
# python plot-covid-19-ecdc.py COVID-19-geographic-disbtribution-worldwide-2020-03-22.xlsx

# Defaults:
normalize = False
start = False
report_cases = True
date = datetime.date.today()
print(date)

def url_for_date(date):
     return 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + date.isoformat() + '.xlsx'

path = url_for_date(date)


# Argument handling
arg = 0
nextarg = 1
#print(len(sys.argv))
for option in sys.argv:
     #print(arg)
     #print(option)
     if arg>=nextarg:
          nextarg = nextarg + 1
          #option = sys.argv[arg] if len(sys.argv) > arg else ''
          if option == '-d' or option == '-deaths':
               report_cases = False
          elif option == '-n' or option == '-normalize':
               normalize = True
               print('Normalize data.')
          elif option == '-s' or option == '-start':
               start = True if len(sys.argv) > arg+1 else False
               if start:
                    provided_min_y = float(sys.argv[arg+1])
                    nextarg = nextarg + 1
          elif option == '-t' or option == '-timestamp':
               timestamp = True
          elif option.startswith('-'):
               sys.exit('Usage: py plot-covid-19-ecdc.py [-d|-deaths] [-n|-normalize] [-s|-start <startvalue>] [<url>|<filename>]')
          else:
               path = option
     arg = arg + 1
     
# Handle case where data for today is not available yet, try to use data from yesterday
try:
     df = pd.read_excel(path)
except:
     print(path + ' not found.')
     datebefore = date-timedelta(days=1)
     path = url_for_date(datebefore)
     print('Trying: ' + path)
     df = pd.read_excel(path)

country_dict = {}
# Group by 'GeoId' and not "Countries and territories" because the latter has
# inconsistent capitalization ('CANADA' and 'Canada').
for country, group in df.groupby(group_by):
     if country in countries:
          # Reverse the time order for each group
          df2 = group.iloc[::-1][[date_column, column]]
          value = df2[column].cumsum() * (1000000 / population[country] if normalize else 1) 
          df2['cum'] = value
          df2 = df2.loc[df2['cum'] >= min_y]
          if len(df2) > 1:
               country_dict[country] = df2[[date_column, 'cum']]
          else:
               print('Country', country, 'has too low value, ignored.')

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
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))

# Draw dotted lines indicating doubling in 1-7 days.
for d in range(1, 8):
     x2 = math.log(max_y / min_y) / math.log(pow(2, 1 / d))
     y2 = max_y
     if x2 > max_x - 1:
          x2 = max_x - 1
          y2 = pow(pow(2, 1 / d), x2) * min_y
     ax.add_line(mlines.Line2D([0, x2], [min_y, y2],
                               c='#666', ls='dotted', lw=0.75))

# Plot the selected countries and print the total for each country.
for country in country_dict:
     df2 = country_dict[country]
     c = min(max_x, len(df2))
     ax.plot(range(c), df2['cum'][:c],
             label=country, lw=0.75, marker='.', ms=4)
     print(country, df2.iloc[-1]['cum'])

# change window and default file name to something else than figure 1:
f = plt.gcf()
window_title = 'covid-19-' + column.lower() + '-ecdc' + ('-normalized' if normalize else '') + ('-' + str(date) if timestamp else '')
f.canvas.set_window_title(window_title)

chart_title = 'Coronavirus Total ' + column + (' Normalized (per Mio. Population)' if normalize else '')
chart_source = 'Source: ' + path
plt.title(chart_title)
font = FontProperties()
font.set_size('x-small')
plt.figtext(0.99, 0.01, chart_source, fontproperties=font, horizontalalignment='right')
ax.legend(loc='lower right')
plt.xlim(left=0)
plt.ylim(bottom=min_y)
plt.show()
