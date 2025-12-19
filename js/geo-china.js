---
title: geo script
---
const width = 800,
  height = 600;

// SVG container
const svg = d3.select("#map")
  .append("svg")
  .attr("width", width)
    .attr("height", height);

// 添加Bootstrap spinner加载指示器
const loadingIndicator = d3.select("#map")
    .append("div")
    .attr("class", "loading-indicator text-center")
    .style("position", "absolute")
    .style("top", "50%")
    .style("left", "50%")
    .style("transform", "translate(-50%, -50%)")
    .html(`
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">加载中...</span>
    </div>
    <div class="mt-2">加载地图数据中...</div>
  `);

// Projection and path
const projection = d3.geoMercator()
  .center([104, 35]) // Center on China
  .scale(600)
  .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);

// Load GeoJSON and data
Promise.all([
  d3.json("{{ site.baseurl }}{{ '/lib/china.geojson' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-china-sent.json' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-china-received.json' }}")
]).then(([geoData, sentData, receivedData]) => {
    loadingIndicator.remove();

  const sentCount = {};
  const receivedCount = {};
  const sentDeliveryDays = {};
  const receivedDeliveryDays = {};
  sentData.forEach(d => {
    sentCount[d.province] = d.count;
    sentDeliveryDays[d.province] = d.avgDeliveryDays;
  });
  receivedData.forEach(d => {
    receivedCount[d.province] = d.count;
    receivedDeliveryDays[d.province] = d.avgDeliveryDays;
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
      return `<strong>${d.properties.name}</strong><br>收: ${receivedCount[d.properties.name] || 0}张 平均${receivedDeliveryDays[d.properties.name] || "-"}天</br>发: ${sentCount[d.properties.name] || 0}张 平均${sentDeliveryDays[d.properties.name] || "-"}天`;
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
}).catch(err => {
    loadingIndicator.remove();
    console.error(err)
});
