/**
 * Assessment sync module — WebSocket with polling fallback.
 *
 * Connects to ws://host/ws/assessments/. When server pushes a 'refresh'
 * signal, fetches fresh data from /api/assessments/sync/ and re-renders.
 * Falls back to polling every 10s if WebSocket is unavailable.
 *
 * Usage: RTAssessmentSync.init({ role, csrfToken, filters });
 */
(function() {
    'use strict';

    var _ws = null;
    var _lastHash = null;
    var _pollTimer = null;
    var _role = 'contributor';
    var _csrfToken = '';
    var _syncUrl = '/api/assessments/sync/';
    var _currentFilters = '';
    var _reconnectTimer = null;
    var _usePolling = false;
    var _initialHashCaptured = false;

    function getCookie(name) {
        var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function init(opts) {
        _role = opts.role || 'contributor';
        _csrfToken = opts.csrfToken || getCookie('csrftoken');
        _syncUrl = opts.syncUrl || '/api/assessments/sync/';
        _currentFilters = opts.filters || '';
        _lastHash = null;
        _initialHashCaptured = false;

        connectWebSocket();
    }

    /* ── WebSocket ─────────────────────────────────────────── */

    function getWsUrl() {
        var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        return proto + '//' + location.host + '/ws/assessments/';
    }

    function connectWebSocket() {
        if (_ws) { try { _ws.close(); } catch(e) {} }

        try {
            _ws = new WebSocket(getWsUrl());
        } catch(e) {
            fallbackToPolling();
            return;
        }

        _ws.onopen = function() {
            _usePolling = false;
            stopPolling();
            fetchAndRender();
        };

        _ws.onmessage = function(evt) {
            try {
                var msg = JSON.parse(evt.data);
                if (msg.type === 'refresh') {
                    fetchAndRender();
                }
            } catch(e) {}
        };

        _ws.onclose = function() {
            _ws = null;
            if (!_usePolling) scheduleReconnect();
        };

        _ws.onerror = function() {
            _usePolling = true;
            _ws = null;
            fallbackToPolling();
        };
    }

    function scheduleReconnect() {
        if (_reconnectTimer) clearTimeout(_reconnectTimer);
        _reconnectTimer = setTimeout(function() {
            if (!_usePolling) connectWebSocket();
        }, 3000);
    }

    /* ── Polling fallback ──────────────────────────────────── */

    function fallbackToPolling() {
        if (_pollTimer) return;
        _pollTimer = setInterval(fetchAndRender, 10000);
    }

    function stopPolling() {
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
    }

    /* ── Data fetch + render ───────────────────────────────── */

    function fetchAndRender(force) {
        var url = _syncUrl + (_currentFilters ? ('?' + _currentFilters) : '');
        fetch(url, { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!_initialHashCaptured) {
                    _lastHash = data.hash;
                    _initialHashCaptured = true;
                    return;
                }
                if (data.hash !== _lastHash) {
                    _lastHash = data.hash;
                    renderTable(data);
                    updateStats(data.stats);
                }
            })
            .catch(function() {});
    }

    function getBadgeClass(status) {
        if (status === 'approved') return 'rt-badge-approved';
        if (status === 'submitted') return 'rt-badge-submitted';
        if (status === 'rejected') return 'rt-badge-rejected';
        return 'rt-badge-draft';
    }

    function renderTable(data) {
        var tbody = document.querySelector('#assessmentsTable tbody');
        if (!tbody) return;

        var rows = data.assessments;
        if (!rows || rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10">' +
                '<div class="rt-empty-state">' +
                '<div class="rt-empty-icon"><i class="fas fa-clipboard"></i></div>' +
                '<h5>No assessments found</h5>' +
                '<p>No assessments match your current filters.</p>' +
                '</div></td></tr>';
            return;
        }

        var html = '';
        for (var i = 0; i < rows.length; i++) {
            var a = rows[i];
            var badgeClass = getBadgeClass(a.status);

            var canDelete = false;
            var canApprove = false;
            if (_role === 'admin') {
                canDelete = (a.status === 'rejected');
                canApprove = (a.status === 'submitted');
            } else if (_role === 'contributor') {
                canDelete = (a.status === 'submitted' || a.status === 'rejected');
            }

            html += '<tr class="assess-row" data-id="' + a.id + '" data-status="' + a.status + '">';

            if (_role === 'admin') {
                html += '<td>';
                if (a.status === 'rejected' || a.status === 'draft') {
                    html += '<input type="checkbox" class="form-check-input assess-check" value="' + a.id + '">';
                }
                html += '</td>';
            }

            html += '<td><span class="badge bg-secondary">#' + a.id + '</span></td>';
            html += '<td><strong>' + escapeHtml(a.barangay) + '</strong><br><small class="text-muted">' + escapeHtml(a.municipality) + '</small></td>';
            html += '<td>' + a.date + '</td>';
            html += '<td><small>' + escapeHtml(a.uploaded_by) + '</small></td>';
            html += '<td>' + (a.reviewed_by ? '<small>' + escapeHtml(a.reviewed_by) + '</small>' : '<small class="text-muted">\u2014</small>') + '</td>';
            html += '<td>' + a.transect_count + '</td>';
            html += '<td>' + (a.coral_cover != null ? a.coral_cover + '%' : '\u2014') + '</td>';
            html += '<td><span class="rt-badge ' + badgeClass + '">' + escapeHtml(a.status_display) + '</span></td>';

            html += '<td><div class="rt-action-group">';
            if (_role === 'admin') {
                html += '<a href="/manage/assessments/' + a.id + '/" class="rt-action-btn rt-action-btn-view" title="View assessment"><i class="fas fa-eye"></i> <span class="btn-label">View</span></a>';
                if (canApprove) {
                    html += '<a href="/manage/assessments/' + a.id + '/confirm-approval/" class="rt-action-btn rt-action-btn-review" title="Review & approve"><i class="fas fa-check"></i> <span class="btn-label">Review</span></a>';
                }
                if (canDelete) {
                    html += '<form method="POST" action="/assessment/' + a.id + '/delete/" class="d-inline">';
                    html += '<input type="hidden" name="csrfmiddlewaretoken" value="' + _csrfToken + '">';
                    html += '<button type="submit" class="rt-action-btn rt-action-btn-delete" title="Delete assessment" onclick="return confirm(\'Delete Assessment #' + a.id + '? This cannot be undone.\')"><i class="fas fa-trash"></i></button>';
                    html += '</form>';
                }
            } else if (_role === 'curator') {
                html += '<a href="/curator/assessments/' + a.id + '/" class="rt-action-btn rt-action-btn-view" title="View assessment"><i class="fas fa-eye"></i> <span class="btn-label">View</span></a>';
                if (canApprove) {
                    html += '<a href="/curator/assessments/' + a.id + '/confirm-approval/" class="rt-action-btn rt-action-btn-review" title="Review & approve"><i class="fas fa-check"></i> <span class="btn-label">Review</span></a>';
                }
            } else {
                html += '<a href="/assessment/' + a.id + '/detail/" class="rt-action-btn rt-action-btn-view" title="View assessment"><i class="fas fa-eye"></i> <span class="btn-label">View</span></a>';
                if (canDelete) {
                    html += '<form method="POST" action="/assessment/' + a.id + '/delete/" class="d-inline">';
                    html += '<input type="hidden" name="csrfmiddlewaretoken" value="' + _csrfToken + '">';
                    html += '<button type="submit" class="rt-action-btn rt-action-btn-delete" title="Delete assessment" onclick="return confirm(\'Delete Assessment #' + a.id + '? This cannot be undone.\')"><i class="fas fa-trash"></i></button>';
                    html += '</form>';
                }
            }
            html += '</div></td></tr>';
        }

        tbody.innerHTML = html;
        rebindCheckboxes();
    }

    function updateStats(stats) {
        var cards = document.querySelectorAll('#statsRow .stat-value');
        if (cards.length >= 5) {
            cards[0].textContent = stats.total;
            cards[1].textContent = stats.submitted;
            cards[2].textContent = stats.approved;
            cards[3].textContent = stats.rejected;
            cards[4].textContent = stats.draft;
        }
    }

    function rebindCheckboxes() {
        var selectAll = document.getElementById('selectAllAssessments');
        var checks = document.querySelectorAll('.assess-check');
        var bulkBtn = document.getElementById('bulkDeleteAssessmentBtn');
        var countSpan = document.getElementById('selectedAssessmentCount');

        if (selectAll) {
            selectAll.onclick = function() {
                var c = this.checked;
                checks.forEach(function(cb) { cb.checked = c; });
                updateBulkBtn();
            };
        }

        checks.forEach(function(cb) {
            cb.onchange = updateBulkBtn;
        });

        function updateBulkBtn() {
            var sel = document.querySelectorAll('.assess-check:checked').length;
            if (countSpan) countSpan.textContent = sel;
            if (bulkBtn) bulkBtn.classList.toggle('d-none', sel === 0);
        }

        if (typeof window.confirmBulkDeleteAssessment === 'function') {
            window.confirmBulkDeleteAssessment = function() {
                var selected = [];
                var skippable = [];
                var form = document.getElementById('bulkDeleteAssessmentForm');
                if (!form) return;
                form.querySelectorAll('input[name="ids"]').forEach(function(e) { e.remove(); });

                document.querySelectorAll('.assess-check:checked').forEach(function(c) {
                    var row = c.closest('.assess-row');
                    var id = c.value;
                    var status = row ? row.getAttribute('data-status') : '';
                    var loc = row ? (row.querySelector('strong') ? row.querySelector('strong').textContent : '') : '';
                    if (status === 'submitted' || status === 'approved') {
                        skippable.push('#' + id + ' ' + loc + ' (' + status + ')');
                    } else {
                        selected.push('#' + id + ' ' + loc + ' (' + status + ')');
                        var input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'ids';
                        input.value = id;
                        form.appendChild(input);
                    }
                });

                if (selected.length === 0 && skippable.length === 0) return;

                var countEl = document.getElementById('bulkDeleteAssessmentCount');
                var listEl = document.getElementById('bulkDeleteAssessmentList');
                var skipAlert = document.getElementById('bulkSkipAssessmentAlert');
                var skipText = document.getElementById('bulkSkipAssessmentText');

                if (countEl) countEl.textContent = selected.length;
                if (listEl) listEl.innerHTML = selected.map(function(n) {
                    return '<span class="badge bg-danger me-1 mb-1">' + n + '</span>';
                }).join('');
                if (skipAlert && skipText) {
                    if (skippable.length > 0) {
                        skipAlert.classList.remove('d-none');
                        skipText.textContent = skippable.length + ' will be skipped (pending or approved): ' + skippable.join(', ');
                    } else {
                        skipAlert.classList.add('d-none');
                    }
                }
                new bootstrap.Modal(document.getElementById('bulkDeleteAssessmentModal')).show();
            };
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    window.RTAssessmentSync = { init: init };
})();
