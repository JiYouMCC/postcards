var offset = 15;
var gap = 1;
var lineGap = 5;
var size = 15;
var showWeekday = true;
var showMonth = true;
var showYear = true;
var weekinline = 52;
// 使用等宽字体
var fontFamily = "Courier New, monospace";
var dayName = ['日', '一', '二', '三', '四', '五', '六'];
var monthName = ["㋀", "㋁", "㋂", "㋃", "㋄", "㋅", "㋆", "㋇", "㋈", "㋉", "㋊", "㋋"];
var multiplier = 1.5;

function calculateYearlyTotals(data) {
  const yearlyTotals = {};

  data.forEach(item => {
    const year = new Date(item.date).getFullYear();
    if (!yearlyTotals[year]) {
      yearlyTotals[year] = {
        sent: 0,
        received: 0,
        monthlyTotals: {}
      };
    }
    yearlyTotals[year].sent += parseInt(item.sent) || 0;
    yearlyTotals[year].received += parseInt(item.received) || 0;

    // for monthly
    const month = new Date(item.date).getMonth() + 1; // Months are zero-based
    if (!yearlyTotals[year].monthlyTotals[month]) {
      yearlyTotals[year].monthlyTotals[month] = {
        sent: 0,
        received: 0
      };
    }
    yearlyTotals[year].monthlyTotals[month].sent += parseInt(item.sent) || 0;
    yearlyTotals[year].monthlyTotals[month].received += parseInt(item.received) || 0;
  });

  return yearlyTotals;
}

function getEarlistDate(data) {
  if (!data || data.length == 0) {
    return new Date();
  }
  data.sort((a, b) => new Date(a.date) - new Date(b.date));
  return new Date(data[0].date);
}

function generateCalender(data, earlistDate, showSent, showReceived) {
  var dayCount = Math.floor((new Date() - earlistDate) / (1000 * 60 * 60 * 24));
  dayCount = Math.ceil(dayCount / 52 / 7) * 52 * 7; //补全为 52*7 的倍数

  var now = new Date();
  //如果今天不是星期日，留出一周的空格
  //if (now.getDay() != 0) {
  dayCount -= 7
  //}

  var start = new Date();
  start.setDate(now.getDate() - dayCount);
  dayCount += start.getDay(); //补全到星期日

  var date = new Date();
  date.setDate(date.getDate() - dayCount)
  var canvasWidth = offset +
    (showWeekday ? (size + gap) : 0) +
    weekinline * (size + gap) +
    (showYear ? (size * 2 + gap) : 0) +
    offset;
  var canvasHeight = offset + Math.ceil(dayCount / weekinline / 7) * ((showMonth ? (size + gap) : 0) + (size + gap) * 7 + lineGap) - lineGap + offset;

  document.getElementById("myCanvas").innerHTML = "";
  var svg = d3.select("#myCanvas")
    .append("svg")
    .attr("width", canvasWidth)
    .attr("height", canvasHeight);
  var box = svg.append("g");
  var weekdayText = svg.append("g");
  var monthText = svg.append("g");

  if (showWeekday) {
    for (var j = 0; j < dayCount / 7 / weekinline; j++) {
      for (var i = 0; i < 7; i++) {
        weekdayText.append("text")
          .attr("x", offset + size / 2)
          .attr("y", offset + size / 2 + (showMonth ? (size + gap) : 0) + i * (size + gap) +
            j * (lineGap + gap + (showMonth ? (size + gap) : 0) + 7 * (size + gap) - gap)
          )
          .attr("text-anchor", "middle")
          .attr("alignment-baseline", "middle")
          .text(dayName[i])
          .attr("data-localize", "calendar.weekday." + i)
          .attr("font-size", (size - 3) + "px")
          .attr("font-family", fontFamily)
          .attr("fill", "#055");
      }
    }
  }

  for (var i = 0; i <= dayCount; i++) {
    var theData = data.find(i => new Date(i.date).toDateString() == date.toDateString());
    var received = 0;
    var sent = 0;
    if (theData) {
      received = showReceived ? theData.received || 0 : 0;
      sent = showSent ? theData.sent || 0 : 0;
    }

    var baseColor = 0xE; // Base color for the calendar boxes
    var color = "#" +
      (baseColor - Math.min(Math.round(sent * multiplier) + Math.round(received * multiplier), baseColor - 1)).toString(16) +
      (baseColor - Math.min(Math.round(sent * multiplier), baseColor - 1)).toString(16) +
      (baseColor - Math.min(Math.round(received * multiplier), baseColor - 1)).toString(16);
    var x = offset + (showWeekday ? (size + gap) : 0) + (size + gap) * (Math.floor(i / 7));
    var y = offset + (showMonth ? (size + gap) : 0) + (size + gap) * date.getDay();
    var monthY = offset + (size / 2);
    x -= Math.floor(i / 7 / weekinline) * weekinline * (size + gap)
    y += (Math.floor(dayCount / 7 / weekinline) - Math.floor(i / 7 / weekinline)) * ((showMonth ? (size + gap) : 0) + 7 * (size + gap) + lineGap);
    monthY += (Math.floor(dayCount / 7 / weekinline) - Math.floor(i / 7 / weekinline)) * ((showMonth ? (size + gap) : 0) + 7 * (size + gap) + lineGap);

    box.append("rect")
      .attr("x", x)
      .attr("y", y)
      .attr("width", size)
      .attr("height", size)
      .attr("fill", color)
      .attr("rx", size / 8)
      .attr("ry", size / 8)
      .attr("data-bs-toggle", "tooltip")
      .attr("data-bs-html", "true")
      .attr("title", d => {
        const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        const link = (type, count) => {
          if (count == 0) {
            return '';
          }
          return `<br> <i data-feather="inbox"></i> ${type === '收' ? '<span data-localize="Receive">Received:</span>' : '<span data-localize="Send">Sent:</span>' } ${count}<a class='text-decoration-none link-light' href='${type === '收' ? 'received?receivedDateStart' : 'sent?sentDateStart'}=${dateStr}T00%3A00&${type === '收' ? 'receivedDateEnd' : 'sentDateEnd'}=${dateStr}T23%3A59' target='_blank'>🔗</a>`;
        }
        return `<b>${dateStr}</b>${showReceived ? link('收', received) : ''}${showSent ? link('发', sent) : ''}`;
      });
    if (showMonth) {
      if (date.getDate() == 1) {
        monthText.append("text")
          .attr("x", x + size / 2)
          .attr("y", monthY)
          .attr("text-anchor", "middle")
          .attr("alignment-baseline", "central")
          .text(monthName[date.getMonth()])
          .attr("font-size", (size - 3) + "px")
          .attr("font-family", fontFamily)
          .attr("fill", "#055")
          .attr("data-bs-toggle", "tooltip")
          .attr("data-bs-html", "true")
          .attr("data-localize", "calendar.month." + date.getMonth())
          .style("cursor", "pointer")
          .attr("title", d => {
            const month = date.getMonth();
            const year = date.getFullYear();
            const link = (type, count, year, month) => {
              if (count == 0) {
                return '';
              }
              let startDate = `${year}-${String(month+1).padStart(2, '0')}-01T00%3A00`;
              let endDate = `${year}-${String(month+2).padStart(2, '0')}-01T00%3A00`;
              return `<br>${type === '收' ? '<span data-localize="Receive">Received:</span>' : '<span data-localize="Send">Sent:</span>' } ${count}<a class='text-decoration-none link-light' href='${type === '收' ? 'received?receivedDateStart' : 'sent?sentDateStart'}=${startDate}&${type === '收' ? 'receivedDateEnd' : 'sentDateEnd'}=${endDate}' target='_blank'>🔗</a>`;
            }
            let received = 0;
            let sent = 0;
            if (yearlyTotals[year]) {
              if (yearlyTotals[year].monthlyTotals[month + 1]) {
                received = yearlyTotals[year].monthlyTotals[month + 1].received || 0;
                sent = yearlyTotals[year].monthlyTotals[month + 1].sent || 0;
              }
            }
            return `<b>${year}-${date.getMonth() + 1}</b>${showReceived ? link('收', received, year,month) : ''}${showSent ? link('发', sent, year,month) : ''}`;
          });
      }
    }

    date.setDate(date.getDate() + 1);
  }
  if (showYear) {
    for (var j = 0; j < Math.ceil(dayCount / weekinline); j++) {
      var rowStartDate = new Date();
      rowStartDate.setDate(date.getDate() - j * 7 * weekinline); // Calculate the starting date of the row
      var year = rowStartDate.getFullYear(); // Get the year

      // Calculate the vertical center of the row
      var rowCenterY = offset + j * ((showMonth ? (size + gap) : 0) + 7 * (size + gap) + lineGap) + (7 * (size + gap)) / 2 + size;

      // Add year text to the right side of the row
      svg.append("text")
        .attr("x", canvasWidth - size * 2) // Position on the right side
        .attr("y", rowCenterY) // Align to the center of the row
        .attr("text-anchor", "middle")
        .attr("alignment-baseline", "middle")
        .text(year) // Display the year
        .attr("font-size", (size + 2) + "px")
        .attr("font-family", fontFamily)
        .attr("transform", "rotate(90, " + (canvasWidth - size * 2) + ", " + rowCenterY + ")") // Rotate 90 degrees
        .attr("fill", "#055")
        .attr("data-bs-toggle", "tooltip")
        .attr("data-bs-html", "true")
        .style("cursor", "pointer")
        .attr("title", d => {
          const link = (type, count, year) => {
            if (count == 0) {
              return '';
            }
            return `<br>${type === '收' ? '<span data-localize="Receive">Received:</span>' : '<span data-localize="Send">Sent:</span>' } ${count}<a class='text-decoration-none link-light' href='${type === '收' ? 'received?receivedDateStart' : 'sent?sentDateStart'}=${year}-01-01T00%3A00&${type === '收' ? 'receivedDateEnd' : 'sentDateEnd'}=${year}-12-31T23%3A59' target='_blank'>🔗</a>`;
          }
          let received = 0;
          let sent = 0;
          if (yearlyTotals[year]) {
            received = yearlyTotals[year].received || 0;
            sent = yearlyTotals[year].sent || 0;
          }
          return `<b>${year}</b>${showReceived ? link('收', received, year) : ''}${showSent ? link('发', sent, year) : ''}`;
        });
    }
  }
}

function refresh() {
  var showSent = document.getElementById("showSent").checked;
  var showReceived = document.getElementById("showReceived").checked;
  generateCalender(groupedData, getEarlist, showSent, showReceived);
  $(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    let language_code = "en";
    if (Cookies.get("local_language_code")) {
        language_code = Cookies.get("local_language_code");
    }
    localize.localize(language_code)
  });
}

var getEarlist = getEarlistDate(groupedData);
var yearlyTotals = calculateYearlyTotals(groupedData);

refresh();