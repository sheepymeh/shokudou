let width, height, gradient;
function getGradient(ctx, chartArea) {
	const chartWidth = chartArea.right - chartArea.left;
	const chartHeight = chartArea.bottom - chartArea.top;
	if (gradient === null || width !== chartWidth || height !== chartHeight) {
		width = chartWidth;
		height = chartHeight;
		gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
		gradient.addColorStop(0, "rgba(147, 41, 30, 1)");
		gradient.addColorStop(1, "rgba(237, 33, 58, 1)");
	}
	return gradient;
}
let timeLabels = [];
for (let hour = 9; hour < 14; hour++) {
	const start = hour == 9 ? 30 : 0;
	const end = hour == 13 ? 31 : 60;
	for (let minute = start; minute < end; minute += 5)
		timeLabels.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
}

function drawSmallChart() {
	const ctx = document.getElementById('small-chart').getContext('2d');
	return new Chart(ctx, {
		type: 'line',
		data: {
			labels: timeLabels,
			datasets: [{
				backgroundColor: 'rgba(255, 99, 132, 0.2)',
				fill: true,
				tension: .3,
				borderWidth: 1
				// showLine: false
			}]
		},
		options: {
			scales: {
				xAxes: {
					ticks: {
						maxTicksLimit: 5,
						maxRotation: 90,
						minRotation: 90,
					}
				},
				yAxes: {
					beginAtZero: true,
					display: false,
				}
			},
			display: false,
			elements: {
				point:{
					radius: 0
				}
			},
			plugins: {
				legend: {
					display: false
				},
			}
		},
	});
}

function drawBigChart() {
	const ctx = document.getElementById('big-chart').getContext('2d');
	return new Chart(ctx, {
		type: 'line',
		data: {
			labels: timeLabels,
			datasets: [{
				backgroundColor: context => {
					const chart = context.chart;
					const {ctx, chartArea} = chart;
					if (!chartArea) return null;
					return getGradient(ctx, chartArea);
				},
				fill: true,
				tension: .3,
				borderWidth: 1
				// showLine: false
			}]
		},
		options: {
			scales: {
				xAxes: {
					ticks: {
						maxTicksLimit: 9,
						maxRotation: -90,
						minRotation: -90,
						mirror: true,
						font: {
							size: 17
						},
						color: '#ddd',
						z: 1
					},
					grid: {
						drawTicks: false,
						drawBorder: false,
						z: 1
					}
				},
				yAxes: {
					beginAtZero: true,
					display: false,
				}
			},
			display: false,
			elements: {
				point: {
					radius: 0
				}
			},
			plugins: {
				legend: {
					display: false
				},
			},
			maintainAspectRatio: false,
			animation: {
				duration: 0,
			},
			layout: {
				padding: {
					top: 10,
				}
			},
		}
	});
}