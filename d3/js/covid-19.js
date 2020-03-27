function makeXHR({method='GET', url, data, headers, timeout, responseType='json'}) {
  return new Promise((resolve, reject) => {
    const req = new XMLHttpRequest();
    if (timeout)
      req.timeout = timeout;
    for (const evt_type of ['load', 'error', 'abort', 'timeout']) {
      req.addEventListener(evt_type, () => {
        if (evt_type === 'load' && req.status === 200) {
          resolve(req.response);
        }
        else {
          const err = new Error(evt_type);
          err.request = req;
          reject(err);
        }
      });
    }
    req.open(method, url, true);
    for (const h in headers)
      req.setRequestHeader(h, headers[h]);
    req.responseType = responseType;
    req.send(data);
  });
}

function plotData(data, min_y) {
  const max_x = data.reduce((max_x, c) => Math.max(max_x, c[1].length - 1), 0);
  const max_y = data.reduce((max_y, c) => Math.max(max_y, c[1][c[1].length - 1][2]), 0);
  const margin = {top: 5, right: 5, bottom: 20, left: 50};
  const width = 640 - margin.left - margin.right;
  const height = 480 - margin.top - margin.bottom;
  const svg = d3.select('#plot')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
  const xScale = d3.scaleLinear()
        .domain([0, max_x])
        .range([0, width]);
  const yScale = d3.scaleLog()
        .domain([min_y, max_y])
        .nice()
        .range([height, 0]);
  const xAxis = d3.axisBottom(xScale);
  const yAxis = d3.axisLeft(yScale);
  const color = d3.scaleOrdinal(d3.schemeCategory10);
  // Axes
  svg.append('g')
    .attr('class', 'x axis')
    .attr('transform', `translate(0,${height})`)
    .call(xAxis);
  // Don't use scientific notation for the y-axis and add thousand separators
  svg.append('g')
    .attr('class', 'y axis')
    .call(yAxis.ticks(9, ',.0f'));
  // Grid
  svg.append('g')			
    .attr('class', 'grid')
    .attr('transform', `translate(0,${height})`)
    .call(xAxis
          .tickSize(-height)
          .tickFormat(''));
  svg.append('g')			
    .attr('class', 'grid')
    .call(yAxis
          .ticks(3)
          .tickSize(-width)
          .tickFormat(''));
  const line = d3.line();
  const countries = data.map(c => c[0]);
  data = data.map(c => c[1].map((d, i) => [xScale(i), yScale(d[2])]));
  // Draw dotted lines indicating doubling in 1-7 days.
  const doubling = [1, 2, 3, 4, 5, 6, 7].map(d => {
    const growth = Math.pow(2, 1 / d);
    let x2 = Math.log(max_y / min_y) / Math.log(growth);
    let y2 = max_y;
    if (x2 > max_x) {
      x2 = max_x;
      y2 = Math.pow(growth, x2) * min_y;
    }
    return [[xScale(0), yScale(min_y)], [xScale(x2), yScale(y2)]];
  });
  svg.append('g')
    .attr('class', 'line')
    .selectAll('path')
    .data(doubling)
    .enter().append('path')
    .style('stroke-dasharray', '2,2')
    .style('stroke', '#666')
    .attr('d', line);
  // Country lines
  svg.append('g')
    .attr('class', 'line')
    .selectAll('path')
    .data(data)
    .enter().append('path')
    .style('stroke', (_, i) => color(i))
    .attr('d', line);
  const dots = [];
  data.forEach((c, i) => {
    dots.push(...c.map(d => [i, ...d]));
  });
  // Country dots
  svg.append('g')
    .selectAll('.dot')
    .data(dots)
    .enter().append('circle')
    .attr('class', 'dot')
    .style('fill', d => color(d[0]))
    .attr('cx', d => d[1])
    .attr('cy', d => d[2])
    .attr('r', 2);
  // Legend
  const legend = svg.append('g')
        .attr('class', 'legend')
        .selectAll('g')
        .data(countries)
        .enter().append('g')
        .attr('transform', (_, i) =>
              `translate(${width - 40},${height - 15 * (countries.length - i)})`);
  legend.append('line')
    .style('stroke', (_, i) => color(i))
    .attr('x2', 20);
  legend.append('text')
    .attr('dy', '.35em')
    .attr('x', 26)
    .text(d => d);
}

function iso(year, month, day) {
  // ISO format string for date
  return year + '-' + [month, day].map(x => String(x).padStart(2, '0')).join('-');
}

function selectCountries(data, keys, min_y, countries) {
  const groups = data.reduce((map, row) => {
    const geo = row[keys[0]];
    if (countries.indexOf(geo) >= 0) {
      const g = map.get(geo) || [];
      g.push([iso(row[keys[1]], row[keys[2]], row[keys[3]]), row[keys[4]]]);
      map.set(geo, g);
    }
    return map;
  }, new Map());
  groups.forEach(g => {
    // Reverse the time order for each group
    g.reverse();
    // Compute cumulative total
    let total = 0;
    for (const row of g) {
      total += row[1];
      row.push(total);
    }
    // Remove all rows below min_y
    const drop = g.findIndex(x => x[2] >= min_y);
    g.splice(0, drop >= 0 ? drop : g.length);
  });
  countries = countries.map(c => [c, groups.get(c) || []]);
  const max_x = countries.map(c => c[1].length).sort((a, b) => a - b);
  // Limit to 5 days past the second longest (for China)
  if (max_x.length >= 2 && max_x[max_x.length - 2] + 5 < max_x[max_x.length - 1]) {
    const crop = max_x[max_x.length - 2] + 5;
    countries.forEach(c => {
      c[1].length = Math.min(c[1].length, crop);
    });
  }
  return countries;
}

async function loadData(key) {
  // Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource at https://www.ecdc.europa.eu/...xlsx. (Reason: CORS header 'Access-Control-Allow-Origin' missing).
  // const url = 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-2020-03-27.xlsx';
  const url = 'COVID-19-geographic-disbtribution-worldwide-2020-03-27.xlsx';
  const data = await makeXHR({url, responseType: 'arraybuffer'});
  // The ECDC data is in Excel format, use XLSX to read.
  const book = XLSX.read(data, {type: 'array'});
  const sheet = book.Sheets[book.SheetNames[0]];
  // Specify 'Cases' or 'Deaths' to plot the respective property.
  const report_cases = !(key && key.toLowerCase() === 'deaths');
  const min_y = report_cases ? 100 : 10;
  const json = XLSX.utils.sheet_to_json(sheet);
  // Format change on 2020-03-27
  const keys = 'geoId' in json[0] ?
        ['geoId', 'year', 'month', 'day', report_cases ? 'cases' : 'deaths'] :
        ['GeoId', 'Year', 'Month', 'Day', report_cases ? 'Cases' : 'Deaths'];
  plotData(selectCountries(json, keys, min_y,
                           ['US', 'DE', 'IT', 'FR', 'ES', 'CN', 'KR', 'JP']),
           min_y);
}

loadData((new URL(document.location)).searchParams.get('key'));
