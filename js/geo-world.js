---
title: geo script
---
const width = 1026, height = 514;

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
    .style("display", "block")
    .style("z-index", "10000")
    .html(`
    <div class="spinner-border text-primary" role="status">
    </div>
  `);

// Projection and path
const projection = d3.geoNaturalEarth1()
    .center([0, 0])
    .scale(180)
    .translate([width / 2, height / 2]);

const path = d3.geoPath().projection(projection);


// 添加投影外框（海洋/背景）
svg.append("path")
    .datum({ type: "Sphere" })
    .attr("class", "sphere")
    .attr("d", path)
    .attr("fill", "rgba(0, 0, 0, 0.01)")
    .attr("stroke", "#333")
    .attr("stroke-width", 1);


// 确保 #map 容器有相对定位
d3.select("#map").style("position", "relative");

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
        .attr("stroke-width", 0.1)
        .attr("data-bs-toggle", "tooltip")
        .attr("data-bs-html", "true")
        .attr("title", d => {
            if (d.properties.SOVEREIGNT === "China" || d.properties.SOVEREIGNT === "Taiwan") {
                return `<strong>${d.properties.SOVEREIGNT}</strong><br><a class="link-light" href="geo-china">Jump to China Map</a</br>`;
            }
            return `<strong>${d.properties.SOVEREIGNT}</strong><br>📥${receivedCount[d.properties.SOVEREIGNT] || 0}<a class="text-decoration-none link-light" href="received?country=${d.properties.SOVEREIGNT}" target="_blank">🔗</a> avg ${receivedDeliveryDays[d.properties.SOVEREIGNT] || "-"} day(s)</br>📤${sentCount[d.properties.SOVEREIGNT] || 0}<a class="text-decoration-none link-light" href="received?country=${d.properties.SOVEREIGNT}" target="_blank">🔗</a> avg ${sentDeliveryDays[d.properties.SOVEREIGNT] || "-"} day(s)`;
        });


    $('[data-bs-toggle="tooltip"]').tooltip();

    // Checkbox event listeners
    d3.select("#showSent").on("change", function () {
        const display = this.checked ? "block" : "none";
        sentLayer.style("display", display);
    });

    d3.select("#showReceived").on("change", function () {
        const display = this.checked ? "block" : "none";
        receivedLayer.style("display", display);
    });
}).catch(err => {
    loadingIndicator.remove();
    console.error(err)
});