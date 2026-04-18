// 智慧渔场管理系统 - 主JavaScript文件

// API基础URL
const API_BASE_URL = "/api";

// 全局状态
let isLoading = false;
const loadingState = {
  count: 0, // 用于追踪多个并发请求
};

// 显示全局加载指示器
function showLoadingIndicator() {
  loadingState.count++;
  let indicator = document.getElementById("globalLoadingIndicator");
  if (!indicator) {
    indicator = document.createElement("div");
    indicator.id = "globalLoadingIndicator";
    indicator.className = "global-loading-indicator";
    indicator.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-info" role="status">
                    <span class="sr-only">加载中...</span>
                </div>
                <p class="mt-2">加载中...</p>
            </div>
        `;
    document.body.appendChild(indicator);
  }
  indicator.style.display = "flex";
  isLoading = true;
}

// 隐藏全局加载指示器
function hideLoadingIndicator() {
  loadingState.count = Math.max(0, loadingState.count - 1);
  if (loadingState.count === 0) {
    const indicator = document.getElementById("globalLoadingIndicator");
    if (indicator) {
      indicator.style.display = "none";
    }
    isLoading = false;
  }
}

// Toast 通知系统
function showToast(message, type = "info", duration = 3000) {
  const toastContainer =
    document.getElementById("toastContainer") || createToastContainer();

  const toastId = `toast-${Date.now()}`;
  const toastHtml = `
        <div id="${toastId}" class="toast-notification toast-${type}" role="alert">
            <div class="toast-content">
                <i class="toast-icon fas ${getToastIcon(type)}"></i>
                <span class="toast-message">${message}</span>
            </div>
            <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
        </div>
    `;

  toastContainer.insertAdjacentHTML("beforeend", toastHtml);
  const toastElement = document.getElementById(toastId);

  // 动画进入
  setTimeout(() => {
    toastElement.classList.add("show");
  }, 10);

  // 自动移除
  setTimeout(() => {
    toastElement.classList.remove("show");
    setTimeout(() => {
      toastElement.remove();
    }, 300);
  }, duration);
}

// 获取 toast 图标
function getToastIcon(type) {
  const iconMap = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
  };
  return iconMap[type] || "fa-info-circle";
}

// 创建 Toast 容器
function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toastContainer";
  container.className = "toast-container";
  document.body.appendChild(container);
  return container;
}

// 通用 API 调用函数（增强版）
async function apiCall(endpoint, method = "GET", data = null, options = {}) {
  try {
    // 显示加载指示器
    if (options.showLoading !== false) {
      showLoadingIndicator();
    }

    const fetchOptions = {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (data && method !== "GET") {
      fetchOptions.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);

    // 隐藏加载指示器
    if (options.showLoading !== false) {
      hideLoadingIndicator();
    }

    // 检查响应内容类型
    const contentType = response.headers.get("content-type");
    let result;

    if (contentType && contentType.includes("application/json")) {
      result = await response.json();
    } else {
      // 非 JSON 响应（可能是 HTML 错误页面或重定向）
      const text = await response.text();
      console.error(
        `API 返回非 JSON 响应: ${endpoint}`,
        text.substring(0, 200),
      );

      if (!response.ok) {
        // 如果状态码不是 2xx，可能需要重新登录
        if (response.status === 401 || response.status === 403) {
          window.location.href = "/login";
          return { status: "error", message: "会话已过期，请重新登录" };
        }
        throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
      }

      return {
        status: "error",
        message: "服务器返回无效格式的数据",
      };
    }

    // 检查响应状态
    if (!response.ok || (result && result.status === "error")) {
      const errorMessage =
        (result && result.message) || `请求失败 (${response.status})`;
      if (options.showError !== false) {
        showToast(errorMessage, "error");
      }
      if (
        options.errorCallback &&
        typeof options.errorCallback === "function"
      ) {
        options.errorCallback(result);
      }
      return result || { status: "error", message: errorMessage };
    }

    // 显示成功消息（如果需要）
    if (options.successMessage && result && result.status === "success") {
      showToast(options.successMessage, "success");
    }

    // 调用成功回调
    if (
      options.successCallback &&
      typeof options.successCallback === "function"
    ) {
      options.successCallback(result);
    }

    return result;
  } catch (error) {
    console.error(`API 调用失败: ${endpoint}`, error);

    // 隐藏加载指示器
    hideLoadingIndicator();

    // 显示错误提示
    const errorMessage = error.message || "网络错误，请检查连接";
    if (options.showError !== false) {
      showToast(errorMessage, "error");
    }

    return {
      status: "error",
      message: errorMessage,
    };
  }
}

// 按钮状态管理
class ButtonStateManager {
  constructor(buttonElement) {
    this.button = buttonElement;
    this.originalText = buttonElement.textContent;
    this.originalHTML = buttonElement.innerHTML;
    this.isDisabled = false;
  }

  setLoading() {
    this.button.disabled = true;
    this.button.classList.add("is-loading");
    this.button.innerHTML = `<span class="spinner-border spinner-border-sm mr-2"></span>处理中...`;
    this.isDisabled = true;
  }

  setSuccess() {
    this.button.classList.add("is-success");
    this.button.innerHTML = `<i class="fas fa-check mr-2"></i>成功`;
  }

  setError() {
    this.button.classList.add("is-error");
    this.button.innerHTML = `<i class="fas fa-exclamation mr-2"></i>出错`;
  }

  restore() {
    this.button.disabled = false;
    this.button.classList.remove("is-loading", "is-success", "is-error");
    this.button.innerHTML = this.originalHTML;
    this.isDisabled = false;
  }
}

// 显示提示消息（兼容旧代码）
function showNotification(message, type = "info") {
  showToast(message, type);
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return "-";
  const date = new Date(timestamp);
  return date.toLocaleString("zh-CN");
}

// 获取 Dashboard 统计数据
async function getDashboardStats() {
  const result = await apiCall("/dashboard-stats", "GET", null, {
    showLoading: true,
  });
  return result;
}

// 获取所有鱼池
async function getPonds() {
  const result = await apiCall("/ponds");
  return result;
}

// 获取特定鱼池
async function getPond(pondId) {
  const result = await apiCall(`/ponds/${pondId}`);
  return result;
}

// 添加鱼池
async function addPond(pondData) {
  const result = await apiCall("/ponds/add", "POST", pondData, {
    successMessage: "鱼池添加成功",
    showLoading: true,
  });
  return result;
}

// 获取传感器数据
async function getSensorData(pondId) {
  const result = await apiCall(`/sensor-data/${pondId}`);
  return result;
}

// 获取设备列表
async function getDevices(pondId, page = 1, perPage = 20) {
  const result = await apiCall(
    `/devices/${pondId}?page=${page}&per_page=${perPage}`,
  );
  return result;
}

// 控制设备
async function controlDevice(deviceId, action, operator = "系统") {
  const controlData = {
    action: action,
    operator: operator,
    details: `${operator}执行了${action}操作`,
  };
  const result = await apiCall(
    `/devices/${deviceId}/control`,
    "POST",
    controlData,
  );
  return result;
}

// 页面加载完成时执行
document.addEventListener("DOMContentLoaded", function () {
  console.log("🐟 智慧渔场管理系统已加载");

  // 检查后端连接状态
  apiCall("/health").then((data) => {
    if (data.status === "success") {
      console.log("✓ 后端服务正常");
    } else {
      console.warn("⚠ 后端连接异常:", data.message);
    }
  });
});

// ECharts 初始化函数
function initECharts(containerId, chartType = "line") {
  const container = document.getElementById(containerId);
  if (!container) return null;

  const myChart = echarts.init(container);

  return myChart;
}

// 绘制水温曲线图
function drawTemperatureChart(containerId, data) {
  const myChart = initECharts(containerId);

  const option = {
    title: { text: "水温变化趋势" },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.times },
    yAxis: { type: "value", name: "温度 (℃)" },
    series: [
      {
        data: data.temperatures,
        type: "line",
        smooth: true,
        itemStyle: { color: "#e74c3c" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(231, 76, 60, 0.3)" },
            { offset: 1, color: "rgba(231, 76, 60, 0)" },
          ]),
        },
      },
    ],
  };

  myChart.setOption(option);
  return myChart;
}

// 绘制pH值变化图
function drawPHChart(containerId, data) {
  const myChart = initECharts(containerId);

  const option = {
    title: { text: "pH值变化趋势" },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.times },
    yAxis: { type: "value", name: "pH值" },
    series: [
      {
        data: data.phValues,
        type: "line",
        smooth: true,
        itemStyle: { color: "#3498db" },
        markLine: {
          data: [
            { name: "安全范围", yAxis: 6.5, itemStyle: { color: "#2ecc71" } },
            { name: "安全范围", yAxis: 8.5, itemStyle: { color: "#2ecc71" } },
          ],
        },
      },
    ],
  };

  myChart.setOption(option);
  return myChart;
}

// 绘制溶氧量图表
function drawDOChart(containerId, data) {
  const myChart = initECharts(containerId);

  const option = {
    title: { text: "溶解氧变化趋势" },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.times },
    yAxis: { type: "value", name: "溶氧量 (mg/L)" },
    series: [
      {
        data: data.doValues,
        type: "line",
        smooth: true,
        itemStyle: { color: "#2ecc71" },
        markLine: {
          data: [{ name: "警戒值", yAxis: 3, itemStyle: { color: "#e74c3c" } }],
        },
      },
    ],
  };

  myChart.setOption(option);
  return myChart;
}

// 绘制鱼池分布饼图
function drawPondDistributionChart(containerId, data) {
  const myChart = initECharts(containerId);

  const option = {
    title: { text: "鱼池分布" },
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: "50%",
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.5)",
          },
        },
      },
    ],
  };

  myChart.setOption(option);
  return myChart;
}

// 绘制设备状态柱状图
function drawDeviceStatusChart(containerId, data) {
  const myChart = initECharts(containerId);

  const option = {
    title: { text: "设备状态分布" },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(data),
    },
    yAxis: { type: "value" },
    series: [
      {
        data: Object.values(data),
        type: "bar",
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#667eea" },
            { offset: 1, color: "#764ba2" },
          ]),
        },
      },
    ],
  };

  myChart.setOption(option);
  return myChart;
}

// 防抖函数
function debounce(func, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

// 节流函数
function throttle(func, limit) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// 导出为CSV
function exportToCSV(data, filename) {
  let csv = "";

  // 添加表头
  if (data.length > 0) {
    csv += Object.keys(data[0]).join(",") + "\n";

    // 添加数据行
    data.forEach((row) => {
      csv += Object.values(row).join(",") + "\n";
    });
  }

  // 创建Blob对象
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", filename || "export.csv");
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 页面响应式处理
window.addEventListener(
  "resize",
  debounce(function () {
    // 重新调整ECharts大小
    const charts = document.querySelectorAll("[_echarts_instance_]");
    charts.forEach((chart) => {
      const instance = echarts.getInstanceByDom(chart);
      if (instance) {
        instance.resize();
      }
    });
  }, 200),
);

console.log("✓ main.js 已加载完成");
