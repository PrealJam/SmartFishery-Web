// 智慧渔场管理系统 - 主JavaScript文件

// API基础URL
const API_BASE_URL = '/api';

// 通用API调用函数
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        return result;
    } catch (error) {
        console.error(`API调用失败: ${endpoint}`, error);
        return {
            status: 'error',
            message: error.message
        };
    }
}

// 显示提示消息
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `;
    
    // 在页面顶部显示
    const container = document.querySelector('.content');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        // 3秒后自动关闭
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
}

// 格式化时间
function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN');
}

// 获取Dashboard统计数据
async function getDashboardStats() {
    const result = await apiCall('/dashboard-stats');
    return result;
}

// 获取所有鱼池
async function getPonds() {
    const result = await apiCall('/ponds');
    return result;
}

// 获取特定鱼池
async function getPond(pondId) {
    const result = await apiCall(`/ponds/${pondId}`);
    return result;
}

// 添加鱼池
async function addPond(pondData) {
    const result = await apiCall('/ponds/add', 'POST', pondData);
    return result;
}

// 获取传感器数据
async function getSensorData(pondId) {
    const result = await apiCall(`/sensor-data/${pondId}`);
    return result;
}

// 获取设备列表
async function getDevices(pondId) {
    const result = await apiCall(`/devices/${pondId}`);
    return result;
}

// 控制设备
async function controlDevice(deviceId, action, operator = '系统') {
    const controlData = {
        action: action,
        operator: operator,
        details: `${operator}执行了${action}操作`
    };
    const result = await apiCall(`/devices/${deviceId}/control`, 'POST', controlData);
    return result;
}

// 页面加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('🐟 智慧渔场管理系统已加载');
    
    // 检查后端连接状态
    apiCall('/health')
        .then(data => {
            if (data.status === 'success') {
                console.log('✓ 后端服务正常');
            } else {
                console.warn('⚠ 后端连接异常:', data.message);
            }
        });
});

// ECharts 初始化函数
function initECharts(containerId, chartType = 'line') {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    const myChart = echarts.init(container);
    
    return myChart;
}

// 绘制水温曲线图
function drawTemperatureChart(containerId, data) {
    const myChart = initECharts(containerId);
    
    const option = {
        title: { text: '水温变化趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: data.times },
        yAxis: { type: 'value', name: '温度 (℃)' },
        series: [{
            data: data.temperatures,
            type: 'line',
            smooth: true,
            itemStyle: { color: '#e74c3c' },
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(231, 76, 60, 0.3)' },
                { offset: 1, color: 'rgba(231, 76, 60, 0)' }
            ])}
        }]
    };
    
    myChart.setOption(option);
    return myChart;
}

// 绘制pH值变化图
function drawPHChart(containerId, data) {
    const myChart = initECharts(containerId);
    
    const option = {
        title: { text: 'pH值变化趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: data.times },
        yAxis: { type: 'value', name: 'pH值' },
        series: [{
            data: data.phValues,
            type: 'line',
            smooth: true,
            itemStyle: { color: '#3498db' },
            markLine: {
                data: [
                    { name: '安全范围', yAxis: 6.5, itemStyle: { color: '#2ecc71' } },
                    { name: '安全范围', yAxis: 8.5, itemStyle: { color: '#2ecc71' } }
                ]
            }
        }]
    };
    
    myChart.setOption(option);
    return myChart;
}

// 绘制溶氧量图表
function drawDOChart(containerId, data) {
    const myChart = initECharts(containerId);
    
    const option = {
        title: { text: '溶解氧变化趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: data.times },
        yAxis: { type: 'value', name: '溶氧量 (mg/L)' },
        series: [{
            data: data.doValues,
            type: 'line',
            smooth: true,
            itemStyle: { color: '#2ecc71' },
            markLine: {
                data: [
                    { name: '警戒值', yAxis: 3, itemStyle: { color: '#e74c3c' } }
                ]
            }
        }]
    };
    
    myChart.setOption(option);
    return myChart;
}

// 绘制鱼池分布饼图
function drawPondDistributionChart(containerId, data) {
    const myChart = initECharts(containerId);
    
    const option = {
        title: { text: '鱼池分布' },
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    
    myChart.setOption(option);
    return myChart;
}

// 绘制设备状态柱状图
function drawDeviceStatusChart(containerId, data) {
    const myChart = initECharts(containerId);
    
    const option = {
        title: { text: '设备状态分布' },
        tooltip: { trigger: 'axis' },
        xAxis: {
            type: 'category',
            data: Object.keys(data)
        },
        yAxis: { type: 'value' },
        series: [{
            data: Object.values(data),
            type: 'bar',
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#667eea' },
                    { offset: 1, color: '#764ba2' }
                ])
            }
        }]
    };
    
    myChart.setOption(option);
    return myChart;
}

// 防抖函数
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 导出为CSV
function exportToCSV(data, filename) {
    let csv = '';
    
    // 添加表头
    if (data.length > 0) {
        csv += Object.keys(data[0]).join(',') + '\n';
        
        // 添加数据行
        data.forEach(row => {
            csv += Object.values(row).join(',') + '\n';
        });
    }
    
    // 创建Blob对象
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 页面响应式处理
window.addEventListener('resize', debounce(function() {
    // 重新调整ECharts大小
    const charts = document.querySelectorAll('[_echarts_instance_]');
    charts.forEach(chart => {
        const instance = echarts.getInstanceByDom(chart);
        if (instance) {
            instance.resize();
        }
    });
}, 200));

console.log('✓ main.js 已加载完成');
