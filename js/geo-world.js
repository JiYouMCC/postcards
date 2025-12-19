---
title: geo script
---
const width = 605, height = 605;

// SVG container
const svg = d3.select("#map")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

// 添加海洋背景（球体）
svg.append("circle")
  .attr("cx", width / 2)
  .attr("cy", height / 2)
  .attr("r", 300)
  .attr("fill", "#eeeeee")
  .attr("stroke", "#777777")
  .attr("stroke-width", 2);

// 添加Bootstrap spinner加载指示器
const loadingIndicator = d3.select("#map")
  .append("div")
  .attr("class", "loading-indicator text-center")
  .style("position", "absolute")
  .style("top", "50%")
  .style("left", "50%")
  .style("transform", "translate(-50%, -50%)")
  .style("display", "block")
  .style("z-index", "10000")
  .html(`
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">加载中...</span>
    </div>
    <div class="mt-2">加载地图数据中...</div>
  `);
// 按钮状态管理
function disableButtons() {
  d3.selectAll(".globe-controls button")
    .attr("disabled", true)
    .classed("rotating", true);
}

function enableButtons() {
  d3.selectAll(".globe-controls button")
    .attr("disabled", null)
    .classed("rotating", false);
}
// Projection and path
const projection = d3.geoOrthographic()
  .center([0, 0])
  .scale(300)
  .translate([width / 2, height / 2])
  .rotate([-121, -30]);

const path = d3.geoPath().projection(projection);

// 平滑旋转函数
function rotateGlobe(deltaLon, deltaLat, duration = 800) {
  disableButtons();

  const currentRotate = projection.rotate();
  const targetRotate = [
    currentRotate[0] + deltaLon,
    currentRotate[1] + deltaLat
  ];

  d3.transition()
    .duration(duration)
    .ease(d3.easeCubicInOut)
    .tween("rotate", function() {
      const interpolate = d3.interpolate(currentRotate, targetRotate);
      return function(t) {
        projection.rotate(interpolate(t));
        svg.selectAll("path.province").attr("d", path);
      };
    }).on("end", enableButtons); // 动画结束后隐藏 loading
}

// 确保 #map 容器有相对定位
d3.select("#map").style("position", "relative");

// 添加控制按钮
const controls = d3.select("#map")
  .append("div")
  .attr("class", "globe-controls")
  .style("position", "absolute")
  .style("top", "0px")
  .style("left", "0px")
  .style("z-index", "1000");

controls.append("div")
  .attr("class", "btn-group-vertical")
  .html(`
        <button class="btn btn-primary btn-sm" id="rotateUp">↑</button>
        <div class="btn-group">
            <button class="btn btn-primary btn-sm" id="rotateLeft">←</button>
            <button class="btn btn-secondary btn-sm" id="rotateReset">⌂</button>
            <button class="btn btn-primary btn-sm" id="rotateRight">→</button>
        </div>
        <button class="btn btn-primary btn-sm" id="rotateDown">↓</button>
    `);

// 按钮事件监听
d3.select("#rotateLeft").on("click", () => rotateGlobe(60, 0));
d3.select("#rotateRight").on("click", () => rotateGlobe(-60, 0));
d3.select("#rotateUp").on("click", () => rotateGlobe(0, -60));
d3.select("#rotateDown").on("click", () => rotateGlobe(0, 60));
d3.select("#rotateReset").on("click", () => {
  const currentRotate = projection.rotate();
  d3.transition()
    .duration(800)
    .ease(d3.easeCubicInOut)
    .tween("rotate", function() {
      const interpolate = d3.interpolate(currentRotate, [-121, -30]);
      return function(t) {
        projection.rotate(interpolate(t));
        svg.selectAll("path.province").attr("d", path);
      };
    });
});

// Load GeoJSON and data
Promise.all([
  d3.json("{{ site.baseurl }}{{ '/lib/world.geojson' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-world-sent.json' }}"),
  d3.json("{{ site.baseurl }}{{ '/js/geo-world-received.json' }}")
]).then(([geoData, sentData, receivedData]) => {
  loadingIndicator.remove();


  const sentCount = {};
  const receivedCount = {};
  const sentDeliveryDays = {};
  const receivedDeliveryDays = {};
  sentData.forEach(d => {
    sentCount[d.country] = d.count;
    sentDeliveryDays[d.country] = d.avgDeliveryDays;
  });
  receivedData.forEach(d => {
    receivedCount[d.country] = d.count;
    receivedDeliveryDays[d.country] = d.avgDeliveryDays;
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
      const count = sentCount[d.properties.SOVEREIGNT];
      return count ? sentColorScale(count) : "#fff";
    })
    .attr("opacity", d => {
      const count = sentCount[d.properties.SOVEREIGNT];
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
      const count = receivedCount[d.properties.SOVEREIGNT];
      return count ? receivedColorScale(count) : "#fff";
    })
    .attr("opacity", d => {
      const count = receivedCount[d.properties.SOVEREIGNT];
      return count ? 0.5 : 0;
    });

  // Draw a transparent map with border
  const borderLayer = svg.selectAll(".border")
    .data(geoData.features)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("class", "province border")
    .attr("fill", d => {
      if (d.properties.SOVEREIGNT === "China" || d.properties.SOVEREIGNT === "Taiwan") {
        return "#ffaaaa";
      }
      return "rgba(0, 0, 0, 0.01)";
    })
    .attr("stroke", "#000")
    .attr("stroke-width", 0.5)
    .attr("data-bs-toggle", "tooltip")
    .attr("data-bs-html", "true")
    .attr("title", d => {
      if (d.properties.SOVEREIGNT === "China" || d.properties.SOVEREIGNT === "Taiwan") {
        return `<strong>${d.properties.SOVEREIGNT}</strong><br><a class="link-light" href="geo-china">Jump to China Map</a</br>`;
      }
      return `<strong>${d.properties.SOVEREIGNT}</strong><br>收: ${receivedCount[d.properties.SOVEREIGNT] || 0}张 平均${receivedDeliveryDays[d.properties.SOVEREIGNT] || "-"}天</br>发: ${sentCount[d.properties.SOVEREIGNT] || 0}张 平均${sentDeliveryDays[d.properties.SOVEREIGNT] || "-"}天`;
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