'use strict';

(function () {
	var contentSelector = '#app-content';
	var sidebarSelector = '.pc-sidebar .pc-navbar a.pc-link, .pc-sidebar .pc-navbar a';
	var isNavigating = false;

	function getAbsoluteUrl(url) {
		var a = document.createElement('a');
		a.href = url;
		return a.href;
	}

	function sameOrigin(url) {
		try {
			var u = new URL(url, window.location.href);
			return window.location.origin === u.origin;
		} catch (e) {
			return false;
		}
	}

	function isHtmlResponse(response) {
		var ct = response.headers.get('content-type') || '';
		return ct.indexOf('text/html') !== -1;
	}

	function updateActiveMenu(url) {
		var links = document.querySelectorAll('.pc-sidebar .pc-navbar a');
		var pageUrl = url.split(/[?#]/)[0];
		for (var i = 0; i < links.length; i++) {
			var li = links[i].parentNode;
			if (li && li.classList) {
				li.classList.remove('active');
				if (li.parentNode && li.parentNode.parentNode) {
					li.parentNode.parentNode.classList.remove('active');
				}
			}
			if (links[i].href === pageUrl && links[i].getAttribute('href') !== '') {
				li.classList.add('active');
				if (li.parentNode && li.parentNode.parentNode) {
					li.parentNode.parentNode.classList.add('pc-trigger');
					li.parentNode.parentNode.classList.add('active');
				}
			}
		}
	}

	function reinitializeUI() {
		try {
			if (window.feather && typeof window.feather.replace === 'function') {
				window.feather.replace();
			}
			if (typeof menu_click === 'function') {
				menu_click();
			}
		} catch (e) {}
	}

	function loadScript(src) {
		return new Promise(function (resolve, reject) {
			var s = document.createElement('script');
			s.src = src;
			s.onload = resolve;
			s.onerror = reject;
			document.head.appendChild(s);
		});
	}

	function runPageInitializers() {
		// Payments dashboard charts
		var needsPaymentCharts = document.getElementById('statusChart') || document.getElementById('modeChart') || document.getElementById('revenueTrendChart') || document.getElementById('adminVsProviderChart');
		if (needsPaymentCharts) {
			var ensureCharts = Promise.resolve();
			if (typeof window.Chart === 'undefined') {
				ensureCharts = loadScript('https://cdn.jsdelivr.net/npm/chart.js');
			}
			ensureCharts
				.then(function () {
					if (typeof window.initPaymentDashboardCharts === 'function') {
						window.initPaymentDashboardCharts();
					}
				})
				.catch(function () {
					// If Chart.js fails to load, skip silently; fallback will be a full reload on next navigation
				});
		}

		// Dispatch a custom event in case other pages want to hook
		document.dispatchEvent(new CustomEvent('page:loaded'));
	}

	function swapContentFromHTML(htmlText, targetUrl) {
		var parser = new DOMParser();
		var doc = parser.parseFromString(htmlText, 'text/html');
		var newContent = doc.querySelector(contentSelector);
		if (!newContent) throw new Error('Content container not found in response');

		var current = document.querySelector(contentSelector);
		if (!current) throw new Error('Content container not found in current page');

		// Optional: simple transition
		current.style.opacity = '0';
		setTimeout(function () {
			current.innerHTML = newContent.innerHTML;
			current.style.opacity = '1';
			reinitializeUI();
			updateActiveMenu(targetUrl);
			runPageInitializers();
		}, 120);

		// Update title
		var newTitle = (doc.querySelector('title') || {}).innerText || document.title;
		document.title = newTitle;
	}

	function navigateTo(url, push) {
		if (isNavigating) return;
		isNavigating = true;
		var absolute = getAbsoluteUrl(url);
		var loader = document.querySelector('.loader-bg');
		if (loader) loader.style.opacity = '1';

		fetch(absolute, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
			.then(function (resp) {
				if (!resp.ok || !isHtmlResponse(resp)) throw new Error('Bad response');
				return resp.text();
			})
			.then(function (htmlText) {
				swapContentFromHTML(htmlText, absolute);
				if (push) {
					history.pushState({ url: absolute }, '', absolute);
				}
			})
			.catch(function () {
				window.location.href = absolute; // graceful fallback
			})
			.finally(function () {
				if (loader) loader.style.opacity = '0';
				isNavigating = false;
			});
	}

	function onSidebarClick(e) {
		var anchor = e.target.closest('a');
		if (!anchor) return;
		var href = anchor.getAttribute('href');
		if (!href || href === '#' || href.indexOf('javascript:') === 0) return;
		var abs = getAbsoluteUrl(href);
		if (!sameOrigin(abs)) return; // allow external links

		e.preventDefault();
		navigateTo(abs, true);
	}

	function bindSidebar() {
		var sidebar = document.querySelector('.pc-sidebar');
		if (!sidebar) return;
		sidebar.addEventListener('click', onSidebarClick);
	}

	window.addEventListener('popstate', function (event) {
		var url = (event && event.state && event.state.url) || window.location.href;
		navigateTo(url, false);
	});

	document.addEventListener('DOMContentLoaded', function () {
		bindSidebar();
		updateActiveMenu(window.location.href);
	});
})();


