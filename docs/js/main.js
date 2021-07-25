const CONFIG = {
	stallNames: [
		'Region 1',
		'Region 2',
		'Region 3',
		'Region 4',
		'Region 5',
		'Region 6',
	],
	api: 'https://api.shokudou.ml'
};

const stallList = document.getElementById('list');
const slideover = document.getElementsByTagName('article')[0];

Chart.defaults.font.family = 'Inter, sans-serif';

function removeAllChildNodes(parent) {
	while (parent.firstChild) parent.removeChild(parent.firstChild);
}

async function updateContent() {
	const reqCurrent = await fetch(`${CONFIG.api}/current`);
	const resCurrent = await reqCurrent.json();

	const countTotal = document.getElementById('count-total');

	if (countTotal.firstChild)
		countTotal.removeChild(countTotal.firstChild);
	countTotal.appendChild(document.createTextNode(resCurrent.data.total));

	removeAllChildNodes(stallList);
	CONFIG.stallNames.forEach((stall, idx) => {
		const row = stallList.insertRow();

		const nameRow = row.insertCell()
		nameRow.appendChild(document.createTextNode(stall));

		const dataRow = row.insertCell()
		dataRow.appendChild(document.createTextNode(resCurrent.data[`stall${idx + 1}`]));

		// const timeRow = row.insertCell()
		// timeRow.appendChild(document.createTextNode(resCurrent.data[`stall${idx + 1}`] * resCurrent.data.speed[`stall${idx + 1}`]));
	});

	
	const reqChart = await fetch(`${CONFIG.api}/graph`);
	const resChart = await reqChart.json();
	drawSmallChart(resChart.data);
}
updateContent();
document.getElementById('count-refresh').addEventListener('click', updateContent);

function newCard(title, value) {
	const card = document.createElement('div');
	card.classList.add('card');

	const titleElem = document.createElement('strong');
	titleElem.appendChild(document.createTextNode(title));

	const valueElem = document.createElement('span');
	valueElem.appendChild(document.createTextNode(value));

	card.appendChild(titleElem);
	card.appendChild(valueElem);

	return card;
}

async function totalChart() {
	document.getElementById('small-chart-container').classList.add('open');
	setTimeout(() => {
		document.body.classList.add('show');
		document.getElementById('small-chart-container').classList.add('hide');
	}, 500);

	const req = await fetch(`${CONFIG.api}/graph`);
	const res = await req.json();
	drawBigChart(res.data);

	const d = new Date();
	if (!(d.getHours() > 13 && d.getMinutes() > 30)) {
		const offset = Math.max(0, (d.getHours() * 12 - 114) + Math.ceil(d.getMinutes() / 5));
		if (offset > res.data.length) offset = 0;
		let bestTime = offset;
		for (let i = offset; i < res.data.length; i++) {
			if (res.data[i] < res.data[bestTime]) bestTime = i;
		}
	}

	const timeHeader = document.createElement('h2');
	timeHeader.appendChild(document.createTextNode(`Today's Crowd Data`));
	document.getElementsByTagName('article')[0].appendChild(timeHeader);

	document.getElementsByTagName('article')[0].appendChild(newCard('Best time for lunch', timeLabels[bestTime]));

	const close = document.createElement('div');
	close.appendChild(document.createTextNode('✖'));
	close.id = 'close';
	close.addEventListener('click', () => {
		document.getElementById('small-chart-container').classList.remove('open');
		document.getElementById('small-chart-container').classList.remove('hide');
		document.getElementsByTagName('article')[0].classList.add('slideout');
		setTimeout(() => {
			document.body.classList.remove('show');
			document.getElementsByTagName('article')[0].classList.remove('slideout');
		}, 200);
	});
	document.getElementsByTagName('article')[0].appendChild(close);
}
document.getElementById('small-chart-container').addEventListener('click', totalChart);