D3 Version of COVID-19 Growth Plot
==================================

This version uses [SheetJS js-xlsx](https://github.com/SheetJS/sheetjs) and
[D3](https://d3js.org/) to read the data and to plot the growth in cases and
deaths due to COVID-19.  The required software is loaded from
[Cloudflare](https://www.cloudflare.com/). The [ECDC COVID-19
data](https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide)
first has to be copied to the web server because [Cross-origin resource
sharing](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) prevents
the file from being loaded directly with an `XMLHttpRequest`.

If this directory is installed in the directory `covid-19` of the server
`example.com`, the chart of deaths is requested with this URL:
`https://example.com/covid-19/?key=deaths`

![D3](./d3.png)
