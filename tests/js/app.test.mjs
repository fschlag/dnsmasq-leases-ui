// Exercises the real handlers in static/app.js against a stub DOM.
// ES modules are cached per process, so app.js is imported exactly once here
// and the failure path lives in its own file.
import assert from 'node:assert/strict';
import { before, describe, it } from 'node:test';

import { installDom, rowsOf } from './dom-stub.mjs';

const LEASES = [
	{
		ipAddress: '172.31.77.201',
		macAddress: '02:AA:00:00:00:01',
		name: 'reserved-a',
		staticIP: true,
		leasetime: '2026-09-28 20:13:16',
	},
	{
		ipAddress: '172.31.77.101',
		macAddress: '02:AA:00:00:00:02',
		name: 'dynamic-b',
		staticIP: false,
		leasetime: '2026-09-28 20:13:19',
	},
	{
		ipAddress: '172.31.77.203',
		macAddress: '02:AA:00:00:00:03',
		name: 'reserved-c',
		staticIP: true,
		leasetime: 'Never',
	},
	{
		ipAddress: '172.31.77.5',
		macAddress: '02:AA:00:00:00:04',
		name: 'zulu',
		staticIP: false,
		leasetime: '2026-09-28 20:13:22',
	},
];

let dom;
const header = key => dom.headers.find(th => th.dataset.key === key);
const names = () => rowsOf(dom.tbody).map(cells => cells[2]);

before(async () => {
	dom = installDom({ leases: LEASES });
	await import('../../static/app.js');
});

describe('initial load', () => {
	it('renders every lease', () => {
		assert.equal(dom.tbody.children.length, 4);
	});

	it('sorts by address numerically, not lexicographically', () => {
		// .5 first, although '5' > '101' as a string.
		assert.deepEqual(names(), ['zulu', 'dynamic-b', 'reserved-a', 'reserved-c']);
	});

	it('shows the real lease end, not "Never", for a reservation', () => {
		const reservedA = rowsOf(dom.tbody).find(cells => cells[2] === 'reserved-a');
		assert.deepEqual(reservedA.slice(3), ['Yes', '2026-09-28 20:13:16']);
	});

	it('reports the count', () => {
		assert.equal(dom.statusEl.textContent, '4 leases');
	});

	it('marks the sorted column for assistive tech', () => {
		assert.equal(header('ipAddress').getAttribute('aria-sort'), 'ascending');
		assert.equal(header('name').getAttribute('aria-sort'), 'none');
	});
});

describe('clicking a header', () => {
	it('sorts by that column', () => {
		dom.thead.dispatch('click', { target: header('name') });
		assert.deepEqual(names(), ['dynamic-b', 'reserved-a', 'reserved-c', 'zulu']);
		assert.equal(header('name').getAttribute('aria-sort'), 'ascending');
	});

	it('flips direction on a second click', () => {
		dom.thead.dispatch('click', { target: header('name') });
		assert.deepEqual(names(), ['zulu', 'reserved-c', 'reserved-a', 'dynamic-b']);
		assert.equal(header('name').getAttribute('aria-sort'), 'descending');
	});

	it('persists the choice', () => {
		assert.deepEqual(JSON.parse(dom.store.get('dnsmasq-leases-sort')), {
			column: 'name',
			dir: 'desc',
		});
	});

	it('responds to Enter as well as a click', () => {
		let prevented = false;
		dom.thead.dispatch('keydown', {
			key: 'Enter',
			target: header('staticIP'),
			preventDefault: () => {
				prevented = true;
			},
		});
		assert.ok(prevented);
		assert.deepEqual(names().slice(0, 2), ['reserved-a', 'reserved-c']);
	});

	it('ignores other keys', () => {
		const before = names();
		dom.thead.dispatch('keydown', { key: 'a', target: header('name'), preventDefault: () => {} });
		assert.deepEqual(names(), before);
	});
});

describe('the filter box', () => {
	it('narrows the table and the count', () => {
		dom.searchEl.value = 'reserved';
		dom.searchEl.dispatch('input');
		assert.deepEqual(names().sort(), ['reserved-a', 'reserved-c']);
		assert.equal(dom.statusEl.textContent, '2 of 4 leases');
	});

	it('restores everything when cleared', () => {
		dom.searchEl.value = '';
		dom.searchEl.dispatch('input');
		assert.equal(dom.tbody.children.length, 4);
		assert.equal(dom.statusEl.textContent, '4 leases');
	});
});

describe('the theme button', () => {
	it('switches to dark and remembers it', () => {
		dom.themeBtn.dispatch('click');
		assert.equal(dom.root.getAttribute('data-theme'), 'dark');
		assert.equal(dom.store.get('dnsmasq-leases-theme'), 'dark');
	});

	it('switches back', () => {
		dom.themeBtn.dispatch('click');
		assert.equal(dom.root.getAttribute('data-theme'), 'light');
		assert.equal(dom.store.get('dnsmasq-leases-theme'), 'light');
	});
});
