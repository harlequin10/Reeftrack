/**
 * Assessment sync polling module.
 * Polls /api/assessments/sync/ and updates the table + stats when data changes.
 * Usage: include this script, then call RTAssessmentSync.init({ role, csrfToken }).
 */
(function() {
    'use strict';

    var _lastHash = null;
    var _pollTimer = null;
    var _interval = 10000;
    var _role = 'contributor';
    var _csrfToken = '';
    var _syncUrl = '/api/assessments/sync/';
    var _currentFilters = '';

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
        startPolling();
    }

    function startPolling() {
        if (_pollTimer) clearInterval(_pollTimer);
        _pollTimer = setInterval(poll, _interval);
        poll();
    }

    function stopPolling() {
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
    }

    function poll() {
        var url = _syncUrl + (_currentFilters ? ('?' + _currentFilters) : '');
        fetch(url, { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.hash !== _lastHash) {
                    _lastHash = data.hash;
                    if (_lastHash !== null) renderTable(data);
                    updateStats(data.stats);
                    showSyncIndicator();
                }
            })
            .catch(function() {});
    }

    function renderTable(data) {
        var tbody = document.querySelector('#assessmentsTable tbody');
        if (!tbody) return;

        var rows = data.assessments;
        if (!rows || rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4">' +
                '<i class="fas fa-clipboard fa-3x text-muted mb-3 d-block"></i>' +
                '<h5>No assessments found</h5>' +
                '<p class="text-muted">No assessments match your filters.</p></td></tr>';
            return;
        }

        var html = '';
        for (var i = 0; i < rows.length; i++) {
            var a = rows[i];
            var statusClass = '';
            if (a.status === 'approved') statusClass = 'bg-success';
            else if (a.status === 'submitted') statusClass = 'bg-warning text-dark';
            else if (a.status === 'rejected') statusClass = 'bg-danger';
            else statusClass = 'bg-secondary';

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

            html += '<td><strong>' + a.id + '</strong></td>';
            html += '<td><strong>' + escapeHtml(a.barangay) + '</strong><br><small class="text-muted">' + escapeHtml(a.municipality) + '</small></td>';
            html += '<td>' + a.date + '</td>';
            html += '<td>' + escapeHtml(a.uploaded_by) + '</td>';
            html += '<td>' + (a.reviewed_by ? '<small>' + escapeHtml(a.reviewed_by) + '</small>' : '<small class="text-muted">-</small>') + '</td>';
            html += '<td>' + a.transect_count + '</td>';
            html += '<td>' + (a.coral_cover != null ? a.coral_cover + '%' : '-') + '</td>';
            html += '<td><span class="badge ' + statusClass + '">' + a.status_display + '</span></td>';

            html += '<td>';
            if (_role === 'admin') {
                html += '<a href="/manage/assessments/' + a.id + '/" class="btn btn-sm btn-outline-primary me-1"><i class="fas fa-eye"></i> View</a>';
                if (canApprove) {
                    html += '<a href="/manage/assessments/' + a.id + '/confirm-approval/" class="btn btn-sm btn-success me-1" title="Review & Approve"><i class="fas fa-check"></i></a>';
                }
                if (canDelete) {
                    html += '<form method="POST" action="/assessment/' + a.id + '/delete/" class="d-inline">';
                    html += '<input type="hidden" name="csrfmiddlewaretoken" value="' + _csrfToken + '">';
                    html += '<button type="submit" class="btn btn-sm btn-outline-danger" title="Delete" onclick="return confirm(\'Delete Assessment #' + a.id + '? This cannot be undone.\')"><i class="fas fa-trash"></i></button>';
                    html += '</form>';
                }
            } else if (_role === 'curator') {
                html += '<a href="/curator/assessments/' + a.id + '/" class="btn btn-sm btn-outline-primary me-1"><i class="fas fa-eye"></i> View</a>';
                if (canApprove) {
                    html += '<a href="/curator/assessments/' + a.id + '/confirm-approval/" class="btn btn-sm btn-success" title="Review & Approve"><i class="fas fa-check"></i></a>';
                }
            } else {
                html += '<a href="/assessment/' + a.id + '/detail/" class="btn btn-sm btn-outline-primary me-1"><i class="fas fa-eye"></i> View</a>';
                if (canDelete) {
                    html += '<form method="POST" action="/assessment/' + a.id + '/delete/" class="d-inline">';
                    html += '<input type="hidden" name="csrfmiddlewaretoken" value="' + _csrfToken + '">';
                    html += '<button type="submit" class="btn btn-sm btn-outline-danger" onclick="return confirm(\'Delete Assessment #' + a.id + '? This cannot be undone.\')"><i class="fas fa-trash"></i> Delete</button>';
                    html += '</form>';
                }
            }
            html += '</td></tr>';
        }

        tbody.innerHTML = html;
        rebindCheckboxes();
    }

    function updateStats(stats) {
        var map = { 'total': 0, 'submitted': 1, 'approved': 2, 'rejected': 3, 'draft': 4 };
        var cards = document.querySelectorAll('#statsRow .card-body h5');
        if (cards.length >= 5) {
            cards[0].textContent = stats.total;
            cards[1].textContent = stats.submitted;
            cards[2].textContent = stats.approved;
            cards[3].textContent = stats.rejected;
            cards[4].textContent = stats.draft;
        }
    }

    function showSyncIndicator() {
        var el = document.getElementById('syncIndicator');
        if (!el) {
            el = document.createElement('span');
            el.id = 'syncIndicator';
            el.style.cssText = 'position:fixed;top:12px;right:12px;background:rgba(0,188,180,0.92);color:#fff;padding:6px 16px;border-radius:20px;font-size:13px;z-index:9999;opacity:0;transition:opacity 0.3s;pointer-events:none;';
            el.innerHTML = '<i class="fas fa-sync-alt"></i> Updated';
            document.body.appendChild(el);
        }
        el.style.opacity = '1';
        setTimeout(function() { el.style.opacity = '0'; }, 2000);
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

    window.RTAssessmentSync = {
        init: init,
        startPolling: startPolling,
        stopPolling: stopPolling,
        poll: poll
    };
})();
