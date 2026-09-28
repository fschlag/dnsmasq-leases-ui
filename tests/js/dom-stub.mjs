// Minimal DOM good enough for static/app.js: enough to dispatch real events at
// the real handlers without a browser. Not a general-purpose fake.

function element(tag) {
	const classes = new Set();
	const listeners = {};
	const self = {
		tag,
		children: [],
		dataset: {},
		value: '',
		textContent: '',
		attributes: {},
		classList: {
			add: c => classes.add(c),
			remove: c => classes.delete(c),
			contains: c => classes.has(c),
		},
		setAttribute: (k, v) => {
			self.attributes[k] = v;
		},
		getAttribute: k => self.attributes[k] ?? null,
		appendChild: c => self.children.push(c),
		replaceChildren: (...c) => {
			self.children = c;
		},
		addEventListener: (type, fn) => {
			(listeners[type] ??= []).push(fn);
		},
		dispatch: (type, event) => {
			for (const fn of listeners[type] ?? []) fn(event);
		},
		closest: () => self,
		querySelector: () => self.indicator ?? null,
	};
	return self;
}

export function installDom({ leases = [], ok = true, status = 200, scriptRoot = '' } = {}) {
	const headers = ['ipAddress', 'macAddress', 'name', 'staticIP', 'leasetime'].map(key => {
		const th = element('th');
		th.dataset.key = key;
		th.indicator = element('span');
		return th;
	});

	const tbody = element('tbody');
	const thead = element('thead');
	const statusEl = element('div');
	const searchEl = element('input');
	const themeBtn = element('button');
	const body = element('body');
	body.dataset.scriptRoot = scriptRoot;

	const bySelector = {
		'#theme-toggle': themeBtn,
		'#leases tbody': tbody,
		'#leases thead': thead,
		'#status': statusEl,
		'#search': searchEl,
	};

	const root = element('html');
	const store = new Map();

	globalThis.document = {
		body,
		documentElement: root,
		createElement: element,
		querySelector: sel => bySelector[sel] ?? null,
		querySelectorAll: sel => (sel === '#leases th' ? headers : []),
	};
	globalThis.localStorage = {
		getItem: k => store.get(k) ?? null,
		setItem: (k, v) => store.set(k, v),
	};
	globalThis.matchMedia = () => ({ matches: false });
	globalThis.fetch = async () => ({
		ok,
		status,
		json: async () => ({ leases }),
	});

	return { headers, tbody, thead, statusEl, searchEl, themeBtn, root, store };
}

export const rowsOf = tbody => tbody.children.map(tr => tr.children.map(td => td.textContent));
