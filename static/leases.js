// Pure lease-table logic: no DOM and no fetch, so `node --test` can import it.

const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

export const DEFAULT_SORT = { column: 'ipAddress', dir: 'asc' };

export function ipToTuple(ip) {
	if (typeof ip !== 'string') return [0, 0, 0, 0];
	if (ip.includes('.') && !ip.includes(':')) {
		return ip.split('.').map(p => parseInt(p, 10) || 0);
	}
	return null;
}

export function cmp(a, b, column) {
	const va = a[column];
	const vb = b[column];
	if (column === 'ipAddress') {
		const ta = ipToTuple(va);
		const tb = ipToTuple(vb);
		if (ta && tb) {
			for (let i = 0; i < 4; i++) {
				if (ta[i] !== tb[i]) return ta[i] - tb[i];
			}
			return 0;
		}
		return collator.compare(String(va), String(vb));
	}
	if (column === 'staticIP') {
		if (va === vb) return cmp(a, b, 'ipAddress');
		return va ? -1 : 1;
	}
	return collator.compare(String(va ?? ''), String(vb ?? ''));
}

export function sortLeases(leases, sort) {
	return [...leases].sort((a, b) => {
		const c = cmp(a, b, sort.column);
		return sort.dir === 'desc' ? -c : c;
	});
}

export function matchesFilter(row, query) {
	if (!query) return true;
	const q = query.toLowerCase();
	return (
		row.ipAddress.toLowerCase().includes(q) ||
		row.macAddress.toLowerCase().includes(q) ||
		(row.name || '').toLowerCase().includes(q) ||
		(row.leasetime || '').toLowerCase().includes(q) ||
		(row.staticIP ? 'yes' : 'no').includes(q)
	);
}

// The backend already reports "Never" for an infinite lease, so the lease end
// goes into the table as it comes.
export function cellsFor(row) {
	return [
		row.ipAddress,
		row.macAddress,
		row.name,
		row.staticIP ? 'Yes' : 'No',
		row.leasetime,
	];
}

export function countLabel(shown, total) {
	return shown === total
		? `${total} lease${total === 1 ? '' : 's'}`
		: `${shown} of ${total} leases`;
}
