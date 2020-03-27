#!/usr/bin/python3

import csv
import datetime
import math
import numpy as np
import pandas as pd
from scipy import stats
import sys

# Outputs tab-separated growth in COVID-19 cases or deaths sorted by the
# average daily growth over the last N days.

path = sys.argv[1] if len(sys.argv) > 1 else 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + datetime.date.today().isoformat() + '.xlsx'

df = pd.read_excel(path)

report_cases = True

# Format change on 2020-03-27
group_by = 'geoId' if 'geoId' in df.keys() else 'GeoId'
if report_cases:
     column = 'cases' if 'cases' in df.keys() else 'Cases'
else:
     column = 'deaths' if 'deaths' in df.keys() else 'Deaths'
date_column = 'dateRep' if 'dateRep' in df.keys() else 'DateRep'

# Threshold for including a country
threshold = 500 if report_cases else 20

# Number of days to include.
ndays = 5
rows = []
for country, group in df.groupby(group_by):
     # Reverse the time order for each group
     df2 = group.iloc[::-1][[date_column, column]]
     df2['cum'] = df2[column].cumsum()
     # Exclude the Diamond Princess
     if country == 'JPG11668':
          continue
     if len(df2) < ndays or df2.iloc[-ndays]['cum'] == 0 or df2.iloc[-1]['cum'] < threshold:
          continue
     header = ['ID'] + [t.strftime('%m/%d') for t in df2.iloc[-ndays:][date_column]] + ['Daily']
     x = np.arange(ndays)
     y = np.log(df2.iloc[-ndays:]['cum'])
     slope, _, _, _, _ = stats.linregress(x, y)
     rows.append([country] + list(df2.iloc[-ndays:]['cum']) + [math.exp(slope)])

# print(rows)

rows.sort(reverse=True, key=lambda x: x[ndays + 1])
writer = csv.writer(sys.stdout, delimiter='\t')
writer.writerow(header)
for r in rows:
     r[ndays + 1] = '%.0f%%' % (100 * (r[ndays + 1] - 1))
     writer.writerow(r)
