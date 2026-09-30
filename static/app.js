import { DEFAULT_SORT, cellsFor, countLabel, matchesFilter, sortLeases } from './leases.js';

const SCRIPT_ROOT = document.body.dataset.scriptRoot ?? '';
const THEME_KEY = 'dnsmasq-leases-theme';
const STORAGE_KEY = 'dnsmasq-leases-sort';

const themeBtn = document.querySelector('#theme-toggle');
themeBtn.addEventListener('click', () => {
	const current = document.documentElement.getAttribute('data-theme');
	const effective = current ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
	const next = effective === 'dark' ? 'light' : 'dark';
	document.documentElement.setAttribute('data-theme', next);
	try { localStorage.setItem(THEME_KEY, next); } catch {}
});

let leases = [];
let filterQuery = '';
let currentSort = loadSort();

function loadSort() {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) {
			const parsed = JSON.parse(raw);
			if (parsed?.column && parsed?.dir) return parsed;
		}
	} catch {}
	return { ...DEFAULT_SORT };
}

function saveSort(sort) {
	try { localStorage.setItem(STORAGE_KEY, JSON.stringify(sort)); } catch {}
}

/*
 * Create a clickable link for an IP address.
 *
 * IPv4:
 *   10.16.12.5 -> http://10.16.12.5
 *
 * IPv6:
 *   fd00:77::113 -> http://[fd00:77::113]
 */
function createIpLink(ip) {
	const link = document.createElement('a');

	const isIPv6 = ip.includes(':');
	const host = isIPv6 ? `[${ip}]` : ip;

	link.href = `http://${host}`;
	link.target = '_blank';
	link.rel = 'noopener noreferrer';
	link.textContent = ip;

	return link;
}

function render() {
	const filtered = leases.filter(row => matchesFilter(row, filterQuery));
	const sorted = sortLeases(filtered, currentSort);
	const tbody = document.querySelector('#leases tbody');

	updateCount(filtered.length);

	tbody.replaceChildren(...sorted.map(row => {
		const tr = document.createElement('tr');
		const values = cellsFor(row);

		values.forEach((val, index) => {
			const td = document.createElement('td');

			/*
			 * The first column is the IP Address column.
			 * Turn it into a clickable HTTP link.
			 */
			if (index === 0 && row.ipAddress) {
				td.appendChild(createIpLink(row.ipAddress));
			} else {
				td.textContent = val;
			}

			tr.appendChild(td);
		});

		return tr;
	}));

	updateIndicators();
}

function updateIndicators() {
	for (const th of document.querySelectorAll('#leases th')) {
		const key = th.dataset.key;
		const ind = th.querySelector('.sort-indicator');

		if (key === currentSort.column) {
			th.classList.add('sorted');
			th.setAttribute('aria-sort', currentSort.dir === 'asc' ? 'ascending' : 'descending');
			ind.textContent = currentSort.dir === 'asc' ? ' ▲' : ' ▼';
		} else {
			th.classList.remove('sorted');
			th.setAttribute('aria-sort', 'none');
			ind.textContent = '';
		}
	}
}

function activateHeader(th) {
	const key = th.dataset.key;

	if (currentSort.column === key) {
		currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
	} else {
		currentSort = { column: key, dir: 'asc' };
	}

	saveSort(currentSort);
	render();
}

const statusEl = document.querySelector('#status');

function updateCount(shown) {
	if (statusEl.classList.contains('error')) return;
	statusEl.textContent = countLabel(shown, leases.length);
}

const searchEl = document.querySelector('#search');

searchEl.addEventListener('input', () => {
	filterQuery = searchEl.value.trim();
	render();
});

const thead = document.querySelector('#leases thead');

thead.addEventListener('click', e => {
	const th = e.target.closest('th');
	if (th) activateHeader(th);
});

thead.addEventListener('keydown', e => {
	if (e.key !== 'Enter' && e.key !== ' ') return;

	const th = e.target.closest('th');
	if (!th) return;

	e.preventDefault();
	activateHeader(th);
});

updateIndicators();

try {
	const r = await fetch(`${SCRIPT_ROOT}/leases`);

	if (!r.ok) throw new Error(`HTTP ${r.status}`);

	const data = await r.json();
	leases = data.leases;

	render();
} catch (err) {
	statusEl.textContent = `Failed to load leases: ${err.message}`;
	statusEl.classList.add('error');
	console.error(err);
}
