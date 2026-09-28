// Own file: app.js run its fetch once, at import time.
import assert from 'node:assert/strict';
import { before, describe, it } from 'node:test';

import { installDom } from './dom-stub.mjs';

let dom;

before(async () => {
	dom = installDom({ ok: false, status: 503 });
	await import('../../static/app.js');
});

describe('when /leases is unavailable', () => {
	it('shows the reason instead of an empty table', () => {
		// The backend answers 503 when the leases file cannot be read.
		assert.equal(dom.statusEl.textContent, 'Failed to load leases: HTTP 503');
	});

	it('marks the status as an error so the count cannot overwrite it', () => {
		assert.ok(dom.statusEl.classList.contains('error'));
	});

	it('leaves the table empty', () => {
		assert.equal(dom.tbody.children.length, 0);
	});
});
