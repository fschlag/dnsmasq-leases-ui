// Rows mirror real dnsmasq output (see tests/samples.py).
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
	cellsFor,
	cmp,
	countLabel,
	ipToTuple,
	matchesFilter,
	sortLeases,
} from '../../static/leases.js';

const dynamicB = {
	ipAddress: '172.31.77.101',
	macAddress: '02:AA:00:00:00:02',
	name: 'dynamic-b',
	staticIP: false,
	leasetime: '2026-09-28 21:32:15',
};
const reservedA = {
	ipAddress: '172.31.77.201',
	macAddress: '02:AA:00:00:00:01',
	name: 'reserved-a',
	staticIP: true,
	leasetime: '2026-09-28 21:32:11',
};
const reservedC = {
	ipAddress: '172.31.77.203',
	macAddress: '02:AA:00:00:00:03',
	name: 'reserved-c',
	staticIP: true,
	leasetime: 'Never',
};
const iphoneTwo = {
	ipAddress: 'fd00:77::113',
	macAddress: '18',
	name: 'iPhone-Two',
	staticIP: true,
	leasetime: '2026-09-28 21:29:37',
};
const names = rows => rows.map(r => r.name);

describe('ipToTuple', () => {
	it('splits IPv4 into octets', () => {
		assert.deepEqual(ipToTuple('172.31.77.201'), [172, 31, 77, 201]);
	});

	it('returns null for IPv6 so the collator takes over', () => {
		assert.equal(ipToTuple('fd00:77::113'), null);
	});

	it('survives a non-string', () => {
		assert.deepEqual(ipToTuple(undefined), [0, 0, 0, 0]);
	});
});

describe('cmp on ipAddress', () => {
	it('orders numerically, not lexicographically', () => {
		// The bug this guards: '172.31.77.101' > '172.31.77.201' as strings.
		assert.ok(cmp(dynamicB, reservedA, 'ipAddress') < 0);
	});

	it('treats equal addresses as equal', () => {
		assert.equal(cmp(reservedA, { ...reservedA }, 'ipAddress'), 0);
	});

	it('falls back to string compare when either side is IPv6', () => {
		assert.notEqual(cmp(iphoneTwo, reservedA, 'ipAddress'), 0);
	});
});

describe('cmp on staticIP', () => {
	it('puts reservations first', () => {
		assert.ok(cmp(reservedA, dynamicB, 'staticIP') < 0);
		assert.ok(cmp(dynamicB, reservedA, 'staticIP') > 0);
	});

	it('breaks ties on the address', () => {
		assert.ok(cmp(reservedA, reservedC, 'staticIP') < 0);
	});
});

describe('sortLeases', () => {
	const rows = [reservedC, dynamicB, iphoneTwo, reservedA];

	it('sorts ascending by address', () => {
		assert.deepEqual(names(sortLeases(rows, { column: 'ipAddress', dir: 'asc' })), [
			'dynamic-b',
			'reserved-a',
			'reserved-c',
			'iPhone-Two',
		]);
	});

	it('inverts for desc', () => {
		const asc = names(sortLeases(rows, { column: 'ipAddress', dir: 'asc' }));
		const desc = names(sortLeases(rows, { column: 'ipAddress', dir: 'desc' }));
		assert.deepEqual(desc, [...asc].reverse());
	});

	it('groups reservations before dynamic leases', () => {
		const sorted = sortLeases(rows, { column: 'staticIP', dir: 'asc' });
		assert.deepEqual(sorted.map(r => r.staticIP), [true, true, true, false]);
	});

	it('leaves the input array untouched', () => {
		const before = names(rows);
		sortLeases(rows, { column: 'name', dir: 'desc' });
		assert.deepEqual(names(rows), before);
	});
});

describe('matchesFilter', () => {
	it('passes everything for an empty query', () => {
		assert.ok(matchesFilter(dynamicB, ''));
	});

	it('matches address, mac, name and lease end', () => {
		assert.ok(matchesFilter(dynamicB, '77.101'));
		assert.ok(matchesFilter(dynamicB, '02:aa'));
		assert.ok(matchesFilter(dynamicB, 'DYNAMIC'));
		assert.ok(matchesFilter(reservedC, 'never'));
	});

	it('matches the reservation column by yes/no', () => {
		assert.ok(matchesFilter(reservedA, 'yes'));
		assert.ok(matchesFilter(dynamicB, 'no'));
		assert.ok(!matchesFilter(dynamicB, 'yes'));
	});

	it('tolerates a nameless lease', () => {
		assert.ok(!matchesFilter({ ...dynamicB, name: null }, 'zzz'));
	});

	it('rejects a miss', () => {
		assert.ok(!matchesFilter(dynamicB, 'stranger'));
	});
});

describe('cellsFor', () => {
	it('shows the real lease end for a reservation', () => {
		// The regression that started this: reservations used to render "Never".
		assert.deepEqual(cellsFor(reservedA), [
			'172.31.77.201',
			'02:AA:00:00:00:01',
			'reserved-a',
			'Yes',
			'2026-09-28 21:32:11',
		]);
	});

	it('passes "Never" through for an infinite lease', () => {
		assert.equal(cellsFor(reservedC).at(-1), 'Never');
	});

	it('renders the reservation flag as Yes/No', () => {
		assert.equal(cellsFor(dynamicB)[3], 'No');
	});
});

describe('countLabel', () => {
	it('counts everything when nothing is filtered', () => {
		assert.equal(countLabel(4, 4), '4 leases');
	});

	it('singularises one lease', () => {
		assert.equal(countLabel(1, 1), '1 lease');
	});

	it('shows the filtered subset', () => {
		assert.equal(countLabel(2, 200), '2 of 200 leases');
	});
});
