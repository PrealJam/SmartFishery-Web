// ==================== Dashboard 相关JS ====================

/**
 * 初始化Dashboard图表
 */
function initDashboardCharts(waterQualityData, deviceStatusData, recentData) {
    initWaterQualityChart(waterQualityData);
    initDeviceStatusChart(deviceStatusData);
    initRecentDataChart(recentData);
}

/**
 * 水质指标仪表盘图表
 */
function initWaterQualityChart(data) {
    const chartDom = document.getElementById('waterQualityChart');
    if (!chartDom) return;
    
    const myChart = echarts.init(chartDom, 'light');
    
    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(50, 50, 50, 0.7)',
            borderColor: '#667eea',
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['水温', 'pH值', '溶氧量', '盐度'],
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            }
        },
        yAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#e8e8e8'
                }
            }
        },
        series: [
            {
                name: '当前值',
                data: data.values || [26, 7.5, 8.2, 15],
                type: 'bar',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#667eea'},
                        {offset: 1, color: '#764ba2'}
                    ])
                },
                smooth: true,
                barWidth: '60%',
                borderRadius: [10, 10, 0, 0]
            }
        ]
    };
    
    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

/**
 * 设备状态分布饼图
 */
function initDeviceStatusChart(data) {
    const chartDom = document.getElementById('deviceStatusChart');
    if (!chartDom) return;
    
    const myChart = echarts.init(chartDom, 'light');
    
    const option = {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(50, 50, 50, 0.7)',
            borderColor: '#667eea',
            textStyle: {
                color: '#fff'
            },
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'right',
            left: 'center',
            top: 'center',
            textStyle: {
                color: '#333',
                fontSize: 12
            }
        },
        series: [
            {
                name: '设备状态',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: [10, 10],
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 12,
                        fontWeight: 'bold'
                    }
                },
                data: [
                    {
                        value: data.online || 8,
                        name: '在线',
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                                {offset: 0, color: '#4facfe'},
                                {offset: 1, color: '#00f2fe'}
                            ])
                        }
                    },
                    {
                        value: data.offline || 2,
                        name: '离线',
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                                {offset: 0, color: '#f5576c'},
                                {offset: 1, color: '#f093fb'}
                            ])
                        }
                    },
                    {
                        value: data.running || 6,
                        name: '运行中',
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                                {offset: 0, color: '#43e97b'},
                                {offset: 1, color: '#38f9d7'}
                            ])
                        }
                    }
                ]
            }
        ]
    };
    
    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

/**
 * 最近数据折线图（显示12小时趋势）
 */
function initRecentDataChart(data) {
    const chartDom = document.getElementById('recentDataChart');
    if (!chartDom) return;
    
    const myChart = echarts.init(chartDom, 'light');
    
    // 生成时间标签（12小时）
    const hours = [];
    for (let i = 11; i >= 0; i--) {
        const h = new Date();
        h.setHours(h.getHours() - i);
        hours.push(h.getHours() + ':00');
    }
    
    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(50, 50, 50, 0.7)',
            borderColor: '#667eea',
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: hours,
            boundaryGap: false,
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            }
        },
        yAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#e8e8e8'
                }
            }
        },
        series: [
            {
                name: '水温(℃)',
                data: data.temperature || [24, 25, 26, 25, 27, 26, 28, 27, 26, 25, 26, 25],
                type: 'line',
                smooth: true,
                itemStyle: {
                    color: '#667eea'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: 'rgba(102, 126, 234, 0.3)'},
                        {offset: 1, color: 'rgba(102, 126, 234, 0)'}
                    ])
                }
            },
            {
                name: '溶游量(mg/L)',
                data: data.oxygen || [8.5, 8.3, 7.8, 7.5, 8.0, 8.2, 7.9, 8.1, 8.3, 8.4, 8.2, 8.0],
                type: 'line',\n                smooth: true,\n                itemStyle: {\n                    color: '#764ba2'\n                },\n                areaStyle: {\n                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [\n                        {offset: 0, color: 'rgba(118, 75, 162, 0.3)'},\n                        {offset: 1, color: 'rgba(118, 75, 162, 0)'}\n                    ])\n                }\n            }\n        ]\n    };\n    \n    myChart.setOption(option);\n    window.addEventListener('resize', () => myChart.resize());\n}\n\n// ==================== 通用函数 ====================\n\n/**\n * 加载并显示统计数据\n */\nfunction loadStatistics() {\n    fetch('/api/statistics')\n        .then(response => response.json())\n        .then(data => {\n            if (data.status === 'success') {\n                updateStatistics(data.data);\n            }\n        })\n        .catch(error => console.error('加载统计数据失败:', error));\n}\n\n/**\n * 更新统计信息\n */\nfunction updateStatistics(stats) {\n    const updateElements = {\n        'pond-count': stats.pond_count,\n        'fish-total': stats.total_fish_count,\n        'device-total': stats.total_devices,\n        'device-online': stats.online_devices\n    };\n    \n    for (const [id, value] of Object.entries(updateElements)) {\n        const elem = document.getElementById(id);\n        if (elem) {\n            elem.textContent = value;\n            elem.parentElement.classList.add('animate-zoom-in');\n        }\n    }\n}\n\n/**\n * 格式化日期\n */\nfunction formatDate(date) {\n    const d = new Date(date);\n    const month = String(d.getMonth() + 1).padStart(2, '0');\n    const day = String(d.getDate()).padStart(2, '0');\n    const hours = String(d.getHours()).padStart(2, '0');\n    const minutes = String(d.getMinutes()).padStart(2, '0');\n    return `${d.getFullYear()}-${month}-${day} ${hours}:${minutes}`;\n}\n\n/**\n * 显示通知\n */\nfunction showNotification(message, type = 'info') {\n    const alertDiv = document.createElement('div');\n    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;\n    alertDiv.setAttribute('role', 'alert');\n    alertDiv.innerHTML = `\n        ${message}\n        <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\" aria-label=\"Close\"></button>\n    `;\n    \n    const container = document.querySelector('.main-container');\n    if (container) {\n        container.insertBefore(alertDiv, container.firstChild);\n        setTimeout(() => alertDiv.remove(), 3000);\n    }\n}\n\n/**\n * 初始化页面\n */\ndocument.addEventListener('DOMContentLoaded', function() {\n    // 初始化AOS动画\n    if (typeof AOS !== 'undefined') {\n        AOS.init({\n            duration: 800,\n            once: true,\n            offset: 100\n        });\n    }\n    \n    // 加载统计数据\n    loadStatistics();\n    \n    // 每30秒刷新一次数据\n    setInterval(loadStatistics, 30000);\n});\n\n// ==================== 数据表格处理 ====================\n\n/**\n * 初始化数据表格\n */\nfunction initDataTable(tableId, ajaxUrl, columns) {\n    const table = document.getElementById(tableId);\n    if (!table) return;\n    \n    loadTableData(ajaxUrl, table, columns);\n}\n\n/**\n * 加载表格数据\n */\nfunction loadTableData(url, table, columns) {\n    fetch(url)\n        .then(response => response.json())\n        .then(data => {\n            if (data.status === 'success') {\n                renderTable(table, data.data, columns);\n            }\n        })\n        .catch(error => {\n            console.error('加载表格数据失败:', error);\n            showNotification('加载数据失败，请稍后重试', 'danger');\n        });\n}\n\n/**\n * 渲染表格\n */\nfunction renderTable(table, data, columns) {\n    const tbody = table.querySelector('tbody');\n    if (!tbody) return;\n    \n    tbody.innerHTML = '';\n    \n    if (data.length === 0) {\n        tbody.innerHTML = `<tr><td colspan=\"${columns.length}\" class=\"text-center text-muted\">暂无数据</td></tr>`;\n        return;\n    }\n    \n    data.forEach(item => {\n        const tr = document.createElement('tr');\n        columns.forEach(col => {\n            const td = document.createElement('td');\n            td.textContent = item[col] || '-';\n            tr.appendChild(td);\n        });\n        tbody.appendChild(tr);\n    });\n}\n"