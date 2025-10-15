---
title: geo script
---
const width = 1024,
  height = 512 + 128 + 128 + 64;

// SVG container
const svg = d3.select("#map")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

// Projection and path
const projection = d3.geoMercator()
  .center([104, 35]) // Center on China
  .scale(900)
  .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// Load GeoJSON and data
Promise.all([
  d3.json("{{ site.baseurl }}{{ '/lib/china.geojson' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-sent.json' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-received.json' }}")
]).then(([geoData, sentData, receivedData]) => {
  const sentCount = {};
  const receivedCount = {};
  sentData.forEach(d => {
    sentCount[d.province] = d.count;
  });
  receivedData.forEach(d => {
    receivedCount[d.province] = d.count;
  });

  const sentColorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, d3.max(Object.values(sentCount))]);
  const receivedColorScale = d3.scaleSequential(d3.interpolateGreens).domain([0, d3.max(Object.values(receivedCount))]);

  // Draw provinces for "sent" data
  const sentLayer = svg.selectAll(".sent")
    .data(geoData.features)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("class", "province sent")
    .attr("fill", d => {
      const count = sentCount[d.properties.name];
      return count ? sentColorScale(count) : "#fff";
    })
    .attr("opacity", d => {
      const count = sentCount[d.properties.name];
      return count ? 0.5 : 0;
    });

  // Draw provinces for "received" data
  const receivedLayer = svg.selectAll(".received")
    .data(geoData.features)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("class", "province received")
    .attr("fill", d => {
      const count = receivedCount[d.properties.name];
      return count ? receivedColorScale(count) : "#fff";
    })
    .attr("opacity", d => {
      const count = receivedCount[d.properties.name];
      return count ? 0.5 : 0;
    });

  // Draw a transparent map with border
  const borderLayer = svg.selectAll(".border")
    .data(geoData.features)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("class", "province border")
    .attr("fill", "rgba(0, 0, 0, 0.01)")
    .attr("stroke", "#000")
    .attr("stroke-width", 0.5)
    .attr("data-bs-toggle","tooltip")
    .attr("data-bs-html","true")
    .attr("title", d => {
      return `<strong>${d.properties.name}</strong><br>收: ${receivedCount[d.properties.name] || 0}<br>发: ${sentCount[d.properties.name] || 0}`;
    });
  $('[data-bs-toggle="tooltip"]').tooltip();

  // Checkbox event listeners
  d3.select("#showSent").on("change", function() {
    const display = this.checked ? "block" : "none";
    sentLayer.style("display", display);
  });

  d3.select("#showReceived").on("change", function() {
    const display = this.checked ? "block" : "none";
    receivedLayer.style("display", display);
  });
}).catch(err => console.error(err));
