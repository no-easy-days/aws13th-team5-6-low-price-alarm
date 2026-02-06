const statusEl = document.getElementById("status");
const coinSelect = document.getElementById("coinSelect");
const alertCoin = document.getElementById("alertCoin");
const fromDate = document.getElementById("fromDate");
const toDate = document.getElementById("toDate");
const chartMeta = document.getElementById("chartMeta");
const chartCanvas = document.getElementById("priceChart");
const lastUpdate = document.getElementById("lastUpdate");
const coinCount = document.getElementById("coinCount");
const alertCount = document.getElementById("alertCount");
const statMax = document.getElementById("statMax");
const statMin = document.getElementById("statMin");
const statAvg = document.getElementById("statAvg");
const statDate = document.getElementById("statDate");
const alertList = document.getElementById("alertList");
const renderTime = document.getElementById("renderTime");
const enableNotifications = document.getElementById("enableNotifications");
const demoAlertButton = document.getElementById("demoAlert");

const fmt = new Intl.NumberFormat("ko-KR");
const coinNameById = new Map();

function setStatus(text) {
  statusEl.textContent = text;
}

function setTodayRange() {
  const today = new Date();
  const prior = new Date();
  prior.setDate(today.getDate() - 7);
  toDate.value = today.toISOString().slice(0, 10);
  fromDate.value = prior.toISOString().slice(0, 10);
}

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function drawChart(points) {
  const ctx = chartCanvas.getContext("2d");
  const width = chartCanvas.width = chartCanvas.clientWidth * devicePixelRatio;
  const height = chartCanvas.height = chartCanvas.clientHeight * devicePixelRatio;
  ctx.clearRect(0, 0, width, height);

  if (!points.length) {
    chartMeta.textContent = "No history data for this range.";
    return;
  }

  const prices = points.map((p) => p.trade_price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const padding = 24 * devicePixelRatio;

  ctx.strokeStyle = "rgba(255,255,255,0.2)";
  ctx.lineWidth = 1;
  ctx.strokeRect(padding, padding, width - padding * 2, height - padding * 2);

  ctx.beginPath();
  points.forEach((p, i) => {
    const x = padding + (i / (points.length - 1)) * (width - padding * 2);
    const y = padding + ((max - p.trade_price) / (max - min || 1)) * (height - padding * 2);
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.strokeStyle = "#ffb454";
  ctx.lineWidth = 3 * devicePixelRatio;
  ctx.stroke();

  ctx.fillStyle = "rgba(255, 180, 84, 0.15)";
  ctx.lineTo(width - padding, height - padding);
  ctx.lineTo(padding, height - padding);
  ctx.closePath();
  ctx.fill();

  chartMeta.textContent = `High ${fmt.format(max)} ? Low ${fmt.format(min)} ? Points ${points.length}`;
}

function populateCoins(coins) {
  coinSelect.innerHTML = "";
  alertCoin.innerHTML = "";
  coinNameById.clear();
  coins.forEach((coin) => {
    const option = document.createElement("option");
    option.value = coin.id;
    option.textContent = coin.market;
    coinSelect.appendChild(option);

    const option2 = option.cloneNode(true);
    alertCoin.appendChild(option2);
    coinNameById.set(String(coin.id), coin.market);
  });
  coinCount.textContent = coins.length;
}

async function loadCoins() {
  const coins = await fetchJSON("/coins");
  populateCoins(coins);
  return coins;
}

async function loadHistory() {
  const coinId = coinSelect.value;
  if (!coinId) return;
  setStatus("Loading history...");
  const params = new URLSearchParams({
    from: fromDate.value,
    to: toDate.value,
  });
  const data = await fetchJSON(`/coins/${coinId}/history?${params}`);
  drawChart(data.items || []);
  lastUpdate.textContent = new Date().toLocaleString();
  setStatus("History loaded");
}

async function loadStats() {
  const coinId = coinSelect.value;
  if (!coinId) return;
  const params = new URLSearchParams({
    from: fromDate.value,
    to: toDate.value,
  });
  const data = await fetchJSON(`/coins/${coinId}/stats?${params}`);
  const latest = data.items[data.items.length - 1];
  if (!latest) {
    statMax.textContent = "-";
    statMin.textContent = "-";
    statAvg.textContent = "-";
    statDate.textContent = "-";
    return;
  }
  statMax.textContent = fmt.format(latest.max);
  statMin.textContent = fmt.format(latest.min);
  statAvg.textContent = fmt.format(latest.avg);
  statDate.textContent = latest.date;
}

function renderAlerts(items) {
  alertList.innerHTML = "";
  if (!items.length) {
    alertList.textContent = "No alerts yet.";
    return;
  }
  items.forEach((alert) => {
    const row = document.createElement("div");
    row.className = "alert-item";
    row.innerHTML = `<div>${alert.coin_id} ? ${alert.condition_type}</div><span>${fmt.format(alert.target_price)}</span>`;
    alertList.appendChild(row);
  });
  alertCount.textContent = items.length;
}

async function loadAlerts() {
  const data = await fetchJSON("/alerts");
  renderAlerts(data.items || []);
}

async function createAlert(event) {
  event.preventDefault();
  const payload = {
    coin_id: Number(alertCoin.value),
    condition_type: document.getElementById("alertCondition").value,
    target_price: Number(document.getElementById("alertPrice").value),
  };
  await fetchJSON("/alerts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  document.getElementById("alertPrice").value = "";
  await loadAlerts();
}

async function createDemoAlert() {
  const coinId = Number(alertCoin.value);
  if (!coinId) {
    setStatus("Select a coin first");
    return;
  }
  const payload = {
    coin_id: coinId,
    condition_type: "LT",
    target_price: 100_000_000,
  };
  await fetchJSON("/alerts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadAlerts();
  setStatus("Demo alert created (will trigger on next price fetch)");
}

function updateNotificationButton() {
  if (!("Notification" in window)) {
    enableNotifications.textContent = "Notifications Unsupported";
    enableNotifications.disabled = true;
    return;
  }
  if (Notification.permission === "granted") {
    enableNotifications.textContent = "Notifications Enabled";
    enableNotifications.disabled = true;
    return;
  }
  if (Notification.permission === "denied") {
    enableNotifications.textContent = "Notifications Blocked";
    enableNotifications.disabled = true;
    return;
  }
  enableNotifications.textContent = "Enable Notifications";
  enableNotifications.disabled = false;
}

async function requestNotificationPermission() {
  if (!("Notification" in window)) {
    setStatus("Notifications not supported");
    updateNotificationButton();
    return;
  }
  if (Notification.permission === "granted") {
    updateNotificationButton();
    return;
  }
  const result = await Notification.requestPermission();
  if (result === "granted") {
    setStatus("Notifications enabled");
  } else if (result === "denied") {
    setStatus("Notifications blocked");
  }
  updateNotificationButton();
}

function showAlertNotification(alert) {
  if (!("Notification" in window) || Notification.permission !== "granted") {
    return;
  }
  const coinName = coinNameById.get(String(alert.coin_id)) || `Coin ${alert.coin_id}`;
  const condition = alert.condition_type === "GT" ? ">= " : "<= ";
  const title = "Alert Triggered";
  const body = `${coinName} ${condition}${fmt.format(alert.target_price)}`;
  new Notification(title, { body });
}

function connectAlertSocket() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socketUrl = `${protocol}://${location.host}/alerts/ws`;
  let socket;

  function connect() {
    socket = new WebSocket(socketUrl);
    socket.onmessage = async (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "alert_triggered") {
          showAlertNotification(payload.alert);
          await loadAlerts();
          setStatus("Alert triggered");
        }
      } catch (err) {
        console.error(err);
      }
    };
    socket.onclose = () => {
      setTimeout(connect, 2000);
    };
  }

  connect();
}

async function boot() {
  setTodayRange();
  await loadCoins();
  await loadHistory();
  await loadStats();
  await loadAlerts();
  updateNotificationButton();
  connectAlertSocket();
  renderTime.textContent = new Date().toLocaleString();
}

document.getElementById("loadHistory").addEventListener("click", loadHistory);
document.getElementById("loadStats").addEventListener("click", loadStats);
document.getElementById("refreshAlerts").addEventListener("click", loadAlerts);
document.getElementById("refreshAll").addEventListener("click", boot);
document.getElementById("alertForm").addEventListener("submit", createAlert);
enableNotifications.addEventListener("click", requestNotificationPermission);
demoAlertButton.addEventListener("click", createDemoAlert);

boot().catch((err) => {
  setStatus("Error loading data");
  console.error(err);
});
