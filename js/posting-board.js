---
title: posting board script
---
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const baseUrl = "{{ site.baseurl }}";
const yearSelect = document.getElementById('yearFilter');
const monthSelect = document.getElementById('monthFilter');
const spinner = document.getElementById('boardSpinner');

// 所有明信片数据：[id, YYYY-MM]，由 Jekyll 在构建时生成
const allPostcards = [
  {% for postcard in site.data.received %}["{{ postcard.id }}","{{ postcard.received_date | date: "%Y-%m" }}"],
  {% endfor %}
];

// 提取唯一年份并倒序排列，填充年份选择框
const years = [...new Set(allPostcards.map(p => p[1].slice(0, 4)).filter(Boolean))].sort().reverse();
years.forEach(y => {
  const opt = document.createElement('option');
  opt.value = y;
  opt.textContent = y;
  yearSelect.appendChild(opt);
});

function populateMonths(year) {
  // 保留第一个默认选项（全年），清除其余
  while (monthSelect.options.length > 1) monthSelect.remove(1);

  if (!year) {
    monthSelect.disabled = true;
    monthSelect.value = '';
    return;
  }

  const lang = (typeof Cookies !== 'undefined' && Cookies.get('local_language_code')) || 'zh';
  const isZh = lang === 'zh';

  // 找出该年份有数据的月份
  const availableMonths = [...new Set(
    allPostcards.filter(p => p[1].startsWith(year)).map(p => p[1].slice(5, 7))
  )].sort();

  availableMonths.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = isZh ? `${parseInt(m)}月` : parseInt(m);
    monthSelect.appendChild(opt);
  });
  monthSelect.disabled = false;
}

function getFilteredIds() {
  const year = yearSelect.value;
  const month = monthSelect.value;

  if (!year) {
    // 默认：最近 48 张（数据按升序排列，取末尾 48 条）
    return allPostcards.slice(-48).map(p => p[0]);
  }
  return allPostcards.filter(p => {
    const [y, m] = p[1].split('-');
    if (month) return y === year && m === month;
    return y === year;
  }).map(p => p[0]);
}

// 绘制带弧度的明信片（使用图片并保持原始宽高比）
function drawCurvedPostcardWithImage(x, y, width, height, angle, image) {
  ctx.save();
  ctx.translate(x + width / 2, y + height / 2);
  ctx.rotate(angle * Math.PI / 180);

  const curveOffset = height * 0.05;
  const edgeOffset = width * 0.05;

  ctx.beginPath();
  ctx.moveTo(-width / 2, -height / 2);
  ctx.bezierCurveTo(-width / 4, -height / 2 - curveOffset, width / 4, -height / 2 - curveOffset, width / 2, -height / 2);
  ctx.bezierCurveTo(width / 2 + edgeOffset, -height / 4, width / 2 + edgeOffset, height / 4, width / 2, height / 2);
  ctx.bezierCurveTo(width / 4, height / 2 + curveOffset, -width / 4, height / 2 - curveOffset, -width / 2, height / 2);
  ctx.bezierCurveTo(-width / 2 - edgeOffset, height / 4, -width / 2 - edgeOffset, -height / 4, -width / 2, -height / 2);
  ctx.clip();

  ctx.shadowColor = 'rgba(0,0,0,0.3)';
  ctx.shadowBlur = 15;
  ctx.shadowOffsetX = 5;
  ctx.shadowOffsetY = 5;

  const imgRatio = image.width / image.height;
  const cardRatio = width / height;
  let drawWidth, drawHeight, offsetX, offsetY;

  if (imgRatio > cardRatio) {
    drawHeight = height;
    drawWidth = height * imgRatio;
    offsetX = -(drawWidth - width) / 2;
    offsetY = 0;
  } else {
    drawWidth = width;
    drawHeight = width / imgRatio;
    offsetX = 0;
    offsetY = -(drawHeight - height) / 2;
  }

  ctx.drawImage(image, -width / 2 + offsetX, -height / 2 + offsetY, drawWidth, drawHeight);
  ctx.restore();
}

function drawBoard(images) {
  spinner.style.display = 'none';
  canvas.style.display = '';

  const cols = 8;
  const baseSize = 160 - 16;
  const padding = 80;
  const overlap = 1 - (1024 - padding * 2) / cols / baseSize;
  const step = baseSize * (1 - overlap);
  const rows = Math.ceil(images.length / cols);
  const angleOffset = 10;
  const offset = 10;

  // 根据行数动态调整画布高度
  canvas.width = 1024;
  canvas.height = padding * 2 + rows * step;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#D2B48C";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#8B7B5A";
  ctx.lineWidth = 12;
  ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);
  ctx.strokeStyle = "#bfa77a";
  ctx.lineWidth = 8;
  ctx.strokeRect(16, 16, canvas.width - 32, canvas.height - 32);
  ctx.strokeStyle = "#fff8dc";
  ctx.lineWidth = 4;
  ctx.strokeRect(24, 24, canvas.width - 48, canvas.height - 48);

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const image = images[row * cols + col];
      if (!image || !image.width) continue;

      const imgRatio = image.width / image.height;
      const isHorizontal = imgRatio >= 1;
      const width = isHorizontal ? baseSize : baseSize * imgRatio;
      const height = isHorizontal ? baseSize / imgRatio : baseSize;

      let x = padding + col * step - (baseSize - height) / 2;
      let y = padding + row * step - (baseSize - width) / 2;
      x += (Math.random() - 0.5) * offset;
      y += (Math.random() - 0.5) * offset;

      const angle = (Math.random() - 0.5) * angleOffset;
      drawCurvedPostcardWithImage(x, y, width, height, angle, image);
    }
  }

  if (yearSelect.value) drawStampLabel();
}

const EN_MONTHS_SHORT = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const EN_MONTHS_FULL  = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const ZH_DIGITS = ['〇','一','二','三','四','五','六','七','八','九'];

function toChineseYear(year) {
  return String(year).split('').map(d => ZH_DIGITS[parseInt(d)]).join('');
}

const ZH_MONTHS = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月'];

function getStampLines() {
  const year  = yearSelect.value;
  const month = monthSelect.value;
  const lang  = (typeof Cookies !== 'undefined' && Cookies.get('local_language_code')) || 'zh';
  const isZh  = lang === 'zh';

  if (!year) return null; // 默认"最近"模式不显示印章（由调用方控制）
  if (isZh) {
    const cyear = toChineseYear(year);
    return month ? [cyear, ZH_MONTHS[parseInt(month) - 1]] : [cyear, ''];
  } else {
    return month ? [year, EN_MONTHS_FULL[parseInt(month) - 1]] : [year, ''];
  }
}

// 沿圆弧绘制文字
// isBottom=false: 上弧（角度递增，字符朝外），isBottom=true: 下弧（字符朝外，从右往左排）
function drawArcText(text, radius, centerAngle, isBottom, fontSize) {
  ctx.font = `bold ${fontSize}px cursive`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  const spacing = fontSize * 0.25;
  const chars = [...text];
  const charWidths = chars.map(ch => ctx.measureText(ch).width);
  const totalWidth = charWidths.reduce((a, b) => a + b, 0) + spacing * (chars.length - 1);
  const totalArc = totalWidth / radius;

  if (!isBottom) {
    // 上弧：角度从小到大，旋转 = θ + π/2
    let angle = centerAngle - totalArc / 2;
    for (let i = 0; i < chars.length; i++) {
      const midAngle = angle + charWidths[i] / 2 / radius;
      ctx.save();
      ctx.translate(radius * Math.cos(midAngle), radius * Math.sin(midAngle));
      ctx.rotate(midAngle + Math.PI / 2);
      ctx.fillText(chars[i], 0, 0);
      ctx.restore();
      angle += (charWidths[i] + spacing) / radius;
    }
  } else {
    // 下弧：从右向左排角度，使文字左→右正向阅读，旋转 = θ - π/2
    let angle = centerAngle + totalArc / 2;
    for (let i = 0; i < chars.length; i++) {
      const midAngle = angle - charWidths[i] / 2 / radius;
      ctx.save();
      ctx.translate(radius * Math.cos(midAngle), radius * Math.sin(midAngle));
      ctx.rotate(midAngle - Math.PI / 2);
      ctx.fillText(chars[i], 0, 0);
      ctx.restore();
      angle -= (charWidths[i] + spacing) / radius;
    }
  }
}

function drawStampLabel() {
  const lines = getStampLines();
  if (!lines) return;
  const fontSize = 16;
  const R  = 48;
  const inner = R - 7;
  const cx = canvas.width  - R - 18;
  const cy = canvas.height - R - 18;
  const ink = '#7B1515';

  ctx.save();
  ctx.translate(cx, cy);
  ctx.globalAlpha = 0.65;
  ctx.fillStyle   = ink;
  ctx.strokeStyle = ink;

  // 外圆
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(0, 0, R, 0, Math.PI * 2);
  ctx.stroke();

  // 内圆（双圈效果）
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(0, 0, inner, 0, Math.PI * 2);
  ctx.stroke();

  const textR = inner - fontSize / 2 - 1;
  const hasBottom = !!lines[1];

  // 只有年份时上弧居中，有月份时上下各一弧
  drawArcText(lines[0], textR, -Math.PI / 2, false, fontSize);
  if (hasBottom) drawArcText(lines[1], textR, Math.PI / 2, true, fontSize);

  // 中心装饰
  ctx.font = '14px serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('✦', 0, 0);

  ctx.restore();
}

function loadAndDraw() {
  spinner.style.display = 'block';
  canvas.style.display = 'none';

  const ids = getFilteredIds();
  // 随机打乱顺序
  ids.sort(() => Math.random() - 0.5);

  if (ids.length === 0) {
    spinner.style.display = 'none';
    canvas.style.display = '';
    canvas.width = 1024;
    canvas.height = 200;
    ctx.fillStyle = "#D2B48C";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#555";
    ctx.font = "20px Arial";
    ctx.textAlign = "center";
    ctx.fillText("该月份暂无收到的明信片", canvas.width / 2, canvas.height / 2);
    return;
  }

  const images = [];
  let loadedCount = 0;

  ids.forEach(id => {
    const img = new Image();
    img.onload = img.onerror = () => {
      loadedCount++;
      if (loadedCount === ids.length) drawBoard(images);
    };
    img.src = `${baseUrl}/received/${id}.jpg`;
    images.push(img);
  });
}

yearSelect.addEventListener('change', function () {
  populateMonths(this.value);
  loadAndDraw();
});
monthSelect.addEventListener('change', loadAndDraw);
canvas.addEventListener('click', loadAndDraw);

loadAndDraw();