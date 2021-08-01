const CONFIG = {
	api: 'https://api.shokudou.ml'
};

(async () => {
	const detectorList = document.getElementById('list');
	const dataReq = await fetch(`${CONFIG.api}/status`);
	const data = await dataReq.json();
	console.log(detectorList.firstChild);
	detectorList.removeChild(detectorList.firstElementChild);

	for (const mac of Object.keys(data.battery)) {
		const row = detectorList.insertRow();

		const macCell = row.insertCell();
		macCell.appendChild(document.createTextNode(mac));

		const statusCell = row.insertCell();
		statusCell.innerHTML = data.online.includes(mac) ? '&#x1F7E2;' : '&#x1F534;';

		const batteryCell = row.insertCell();
		batteryCell.appendChild(document.createTextNode(`${Math.round(data.battery[mac] * 100)}%`));
	}
})();