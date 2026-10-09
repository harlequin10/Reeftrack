/* Reusable boundary polygon drawing tool for the location admin forms.
 *
 * Each call to RTGeoDraw.init() wires up a small Leaflet map plus
 * Draw/Undo/Clear buttons and writes the resulting Polygon/MultiPolygon
 * GeoJSON into a hidden form field (name="boundary_json").
 *
 * Draw tools:
 *   Draw / Add Point  — toggle click-to-add on the map; click existing points
 *                       to remove them; double-click the map to stop drawing.
 *   Undo              — remove the last point.
 *   Clear             — remove everything and mark the boundary for removal.
 *   Type Coordinates  — show a textarea that accepts one "lat, lng" point per
 *                       line (or a pasted GeoJSON Polygon/MultiPolygon); Apply
 *                       loads the points onto the map for fine-tuning:
 *                       drag points to adjust, Undo/Clear to revise.
 *
 * Maps are created lazily the first time their modal is shown, so the page
 * can have many modals without paying for tile loads up front.
 */
window.RTGeoDraw = (function () {
  var TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}';
  var TILE_ATTR = 'Tiles &copy; Esri';
  var DEFAULT_CENTER = [7.8, 124.5];
  var DEFAULT_ZOOM = 7;

  function makeVertexIcon(n) {
    return L.divIcon({
      className: '',
      iconSize: [22, 22],
      iconAnchor: [11, 11],
      html: '<div style="width:22px;height:22px;border-radius:50%;background:#0d6efd;color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.5);">' + n + '</div>'
    });
  }

  function makeReferenceIcon() {
    return L.divIcon({
      className: '',
      iconSize: [16, 16],
      iconAnchor: [8, 8],
      html: '<div style="width:16px;height:16px;border-radius:50%;background:#6c757d;opacity:.8;"></div>'
    });
  }

  function largestRing(polygon) {
    var best = null;
    for (var i = 0; i < polygon.length; i++) {
      if (!best || polygon[i].length > best.length) best = polygon[i];
    }
    return best;
  }

  function collectRings(geom) {
    var rings = [];
    if (!geom || !geom.type) return rings;
    if (geom.type === 'Polygon') {
      for (var i = 0; i < geom.coordinates.length; i++) rings.push(geom.coordinates[i]);
    } else if (geom.type === 'MultiPolygon') {
      for (var j = 0; j < geom.coordinates.length; j++) {
        for (var k = 0; k < geom.coordinates[j].length; k++) rings.push(geom.coordinates[j][k]);
      }
    }
    return rings;
  }

  function parseManualText(text, name) {
    var t = (text || '').replace(/^\uFEFF/, '').trim();
    if (!t) return { error: 'Enter at least one coordinate.' };
    if (t.charAt(0) === '{') {
      var parsed, geom;
      try {
        parsed = JSON.parse(t);
      } catch (e) {
        return { error: 'The pasted JSON is not valid. Use "lat, lng" per line, or a GeoJSON Polygon/MultiPolygon.' };
      }
      geom = parsed;
      if (geom && geom.type === 'Feature' && geom.geometry) geom = geom.geometry;
      if (geom && geom.type === 'FeatureCollection' && geom.features && geom.features.length) {
        geom = geom.features[0].geometry;
      }
      if (!geom || (geom.type !== 'Polygon' && geom.type !== 'MultiPolygon')) {
        return { error: 'Pasted JSON must be a GeoJSON Polygon or MultiPolygon.' };
      }
      var rings = collectRings(geom);
      if (!rings.length) return { error: 'The pasted polygon has no coordinates.' };
      var big = largestRing(rings);
      var pts = [];
      for (var r = 0; r < big.length; r++) {
        var lat = Number(big[r][1]);
        var lng = Number(big[r][0]);
        if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
          return { error: 'A pasted coordinate is out of range.' };
        }
        pts.push(L.latLng(lat, lng));
      }
      if (pts.length > 1) {
        var f0 = pts[0], l0 = pts[pts.length - 1];
        if (f0.lat === l0.lat && f0.lng === l0.lng) pts.pop();
      }
      if (pts.length < 3) return { error: 'Need at least 3 points to form a boundary.' };
      return { ring: pts };
    }
    var lines = t.split(/[\r\n;]+/);
    var ringPts = [];
    for (var n = 0; n < lines.length; n++) {
      var line = lines[n].trim();
      if (!line) continue;
      var parts = line.split(/[,\s]+/);
      if (parts.length < 2) return { error: 'Line ' + (n + 1) + ': expected "latitude, longitude".' };
      var la = parseFloat(parts[0]);
      var ln = parseFloat(parts[1]);
      if (isNaN(la) || isNaN(ln)) return { error: 'Line ' + (n + 1) + ': not a valid number.' };
      if (la < -90 || la > 90 || ln < -180 || ln > 180) return { error: 'Line ' + (n + 1) + ': coordinate out of range.' };
      ringPts.push(L.latLng(la, ln));
    }
    if (ringPts.length < 3) return { error: 'Need at least 3 points to form a boundary.' };
    if (ringPts.length > 1) {
      var f = ringPts[0], l = ringPts[ringPts.length - 1];
      if (f.lat === l.lat && f.lng === l.lng) ringPts.pop();
    }
    if (ringPts.length < 3) return { error: 'Need at least 3 points to form a boundary.' };
    return { ring: ringPts };
  }

  function init(opts) {
    var mapEl = document.getElementById(opts.mapEl);
    if (!mapEl) return;

    var drawBtn = document.getElementById(opts.drawBtn);
    var undoBtn = document.getElementById(opts.undoBtn);
    var clearBtn = document.getElementById(opts.clearBtn);
    var manualBtn = document.getElementById(opts.manualBtn);
    var manualWrap = document.getElementById(opts.manualWrap);
    var manualArea = document.getElementById(opts.manualArea);
    var manualApply = document.getElementById(opts.manualApply);
    var manualCancel = document.getElementById(opts.manualCancel);
    var manualErr = document.getElementById(opts.manualErr);
    var input = document.getElementById(opts.input);
    var clearFlag = document.getElementById(opts.clearFlag);
    var statusEl = document.getElementById(opts.status);
    var label = opts.name || 'Location';

    var editor = {
      map: null,
      ring: [],
      markers: [],
      line: null,
      fill: null,
      refs: null,
      drawing: false,
      commitPaused: false,
      created: false
    };

    function setStatus(msg) {
      if (statusEl) statusEl.innerHTML = msg;
    }

    function refreshStatus() {
      if (editor.drawing) {
        setStatus('Add mode is ON &mdash; click the map to add a boundary point. Click an existing point to remove it. Double-click the map to stop.');
        return;
      }
      if (editor.ring.length >= 3) {
        setStatus(editor.ring.length + ' points &mdash; boundary shape ready. Drag any point to adjust, Undo to remove the last one, or Clear to start over.');
      } else if (editor.ring.length > 0) {
        setStatus(editor.ring.length + ' point' + (editor.ring.length === 1 ? '' : 's') + ' &mdash; add at least 3 to form the boundary.');
      } else if (editor.refs && editor.refs.getLayers().length) {
        setStatus('The existing boundary is shown as a reference. Draw, edit, Undo, or load typed coordinates to replace it; leave as is to keep the current boundary.');
      } else {
        setStatus('Optional. No boundary set for this ' + label.toLowerCase() + '.');
      }
    }

    function clearShapes() {
      if (editor.line) editor.map.removeLayer(editor.line);
      if (editor.fill) editor.map.removeLayer(editor.fill);
      if (editor.refs) editor.map.removeLayer(editor.refs);
      editor.line = null;
      editor.fill = null;
      editor.refs = null;
    }

    function addMarkerAt(idx, latlng) {
      var mk = L.marker(latlng, { draggable: true, icon: makeVertexIcon(idx + 1) }).addTo(editor.map);
      (function (i) {
        mk.on('drag', function () {
          editor.ring[i] = mk.getLatLng();
          renderShape();
          commit();
        });
        mk.on('click', function (e) {
          L.DomEvent.stopPropagation(e);
          if (editor.drawing) removePoint(i);
        });
      })(idx);
      editor.markers.push(mk);
      return mk;
    }

    function renumber() {
      for (var i = 0; i < editor.markers.length; i++) {
        editor.markers[i].setIcon(makeVertexIcon(i + 1));
      }
    }

    function commit() {
      if (editor.commitPaused) return;
      clearFlag.value = '';
      if (editor.ring.length < 3) {
        input.value = '';
        return;
      }
      var closed = [];
      for (var i = 0; i < editor.ring.length; i++) {
        var p = editor.ring[i];
        closed.push([p.lng, p.lat]);
      }
      var first = closed[0];
      var last = closed[closed.length - 1];
      if (last[0] !== first[0] || last[1] !== first[1]) closed.push([first[0], first[1]]);
      input.value = JSON.stringify({ type: 'Polygon', coordinates: [closed] });
    }

    function renderShape() {
      clearShapes();
      if (editor.ring.length === 0) return;
      var pts = editor.ring.slice();
      if (pts.length >= 2) {
        editor.line = L.polyline(pts, { color: '#0d6efd', weight: 2.5, dashArray: '6 6' }).addTo(editor.map);
      }
      if (pts.length >= 3) {
        editor.fill = L.polygon(pts, { color: '#0d6efd', weight: 2, fillColor: '#0d6efd', fillOpacity: 0.1 }).addTo(editor.map);
      }
    }

    function addPoint(latlng) {
      editor.commitPaused = false;
      var idx = editor.ring.length;
      editor.ring.push(latlng);
      addMarkerAt(idx, latlng);
      renderShape();
      commit();
      refreshStatus();
    }

    function removePoint(idx) {
      editor.commitPaused = false;
      var mk = editor.markers[idx];
      if (mk) editor.map.removeLayer(mk);
      editor.markers.splice(idx, 1);
      editor.ring.splice(idx, 1);
      renumber();
      renderShape();
      commit();
      refreshStatus();
    }

    function onMapClick(e) {
      if (!editor.drawing) return;
      addPoint(e.latlng);
    }

    function onMapDblClick() {
      if (editor.drawing) {
        editor.drawing = false;
        refreshStatus();
      }
    }

    function stopDrawing() {
      editor.drawing = false;
      if (drawBtn) drawBtn.classList.remove('active');
    }

    function clearAll() {
      stopDrawing();
      editor.commitPaused = false;
      while (editor.markers.length) editor.map.removeLayer(editor.markers.pop());
      editor.ring = [];
      renderShape();
      input.value = '';
      clearFlag.value = '1';
      emptyManualErr();
      refreshStatus();
    }

    function showManualErr(msg) {
      if (manualErr) {
        manualErr.textContent = msg;
        manualErr.style.display = '';
      }
    }

    function emptyManualErr() {
      if (manualErr) manualErr.textContent = '';
    }

    function toggleManual(show) {
      if (manualWrap) manualWrap.classList.toggle('d-none', !show);
      if (show && manualArea) manualArea.focus();
    }

    function applyManual() {
      if (!editor.map) return;
      emptyManualErr();
      var text = manualArea ? manualArea.value : '';
      var result = parseManualText(text, label);
      if (result.error) {
        showManualErr(result.error);
        return;
      }
      stopDrawing();
      editor.commitPaused = false;
      while (editor.markers.length) editor.map.removeLayer(editor.markers.pop());
      editor.ring = result.ring;
      for (var i = 0; i < editor.ring.length; i++) addMarkerAt(i, editor.ring[i]);
      renderShape();
      commit();
      var bounds = [];
      for (var j = 0; j < editor.ring.length; j++) {
        bounds.push([editor.ring[j].lat, editor.ring[j].lng]);
      }
      editor.map.fitBounds(L.latLngBounds(bounds), { padding: [25, 25] });
      setStatus(editor.ring.length + ' points loaded from your text. Drag any point to adjust, or Undo/Clear to revise.');
      toggleManual(false);
    }

    

    function createMap() {
      if (editor.created) return;
      editor.created = true;
      editor.map = L.map(mapEl, { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, minZoom: 4, maxZoom: 18 });
      L.tileLayer(TILE_URL, { attribution: TILE_ATTR, maxZoom: 18, maxNativeZoom: 16 }).addTo(editor.map);
      editor.map.on('click', onMapClick);
      editor.map.on('dblclick', onMapDblClick);
      loadInitial();
    }

    function loadInitial() {
      var initial = opts.initial;
      if (!initial || !initial.type) {
        editor.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        refreshStatus();
        return;
      }
      if (initial.type === 'Point') {
        L.marker([initial.coordinates[1], initial.coordinates[0]], { icon: makeReferenceIcon() }).addTo(editor.map);
        editor.map.setView([initial.coordinates[1], initial.coordinates[0]], 14);
        editor.commitPaused = true;
        if (editor.refs === null) editor.refs = L.layerGroup().addTo(editor.map);
        refreshStatus();
        return;
      }
      var rings = collectRings(initial);
      if (!rings.length) {
        editor.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
        refreshStatus();
        return;
      }
      var big = largestRing(rings);
      var isSingle = initial.type === 'Polygon' && rings.length === 1;
      var bounds = [];
      var refLayers = [];
      for (var r = 0; r < rings.length; r++) {
        var ring = rings[r];
        var ll = [];
        for (var q = 0; q < ring.length; q++) {
          ll.push([ring[q][1], ring[q][0]]);
          bounds.push([ring[q][1], ring[q][0]]);
        }
        if (r !== 0 || !isSingle) {
          refLayers.push(L.polyline(ll, { color: '#6c757d', weight: 1.5, dashArray: '4 4' }));
        }
      }
      if (refLayers.length) editor.refs = L.layerGroup(refLayers).addTo(editor.map);
      if (big && big.length >= 3) {
        editor.ring = [];
        for (var m = 0; m < big.length; m++) {
          editor.ring.push(L.latLng(big[m][1], big[m][0]));
        }
        for (var n = 0; n < editor.ring.length; n++) addMarkerAt(n, editor.ring[n]);
        renderShape();
        if (isSingle) {
          commit();
        } else {
          editor.commitPaused = true;
        }
      }
      if (bounds.length) {
        editor.map.fitBounds(L.latLngBounds(bounds), { padding: [25, 25] });
      } else {
        editor.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
      }
      refreshStatus();
    }

    if (drawBtn) {
      drawBtn.addEventListener('click', function () {
        if (!editor.created) createMap();
        editor.drawing = !editor.drawing;
        drawBtn.classList.toggle('active', editor.drawing);
        refreshStatus();
      });
    }
    if (undoBtn) {
      undoBtn.addEventListener('click', function () {
        if (!editor.created) createMap();
        if (editor.markers.length) removePoint(editor.markers.length - 1);
      });
    }
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        if (!editor.created) createMap();
        clearAll();
      });
    }
    if (manualBtn) {
      manualBtn.addEventListener('click', function () {
        var isHidden = !manualWrap || manualWrap.classList.contains('d-none');
        toggleManual(isHidden);
      });
    }
    if (manualCancel) {
      manualCancel.addEventListener('click', function () {
        emptyManualErr();
        toggleManual(false);
      });
    }
    if (manualApply) {
      manualApply.addEventListener('click', function () {
        applyManual();
      });
    }

    var modalEl = null;
    var node = mapEl;
    while (node && node !== document) {
      if (node.classList && node.classList.contains('modal')) { modalEl = node; break; }
      node = node.parentNode;
    }
    if (modalEl) {
      modalEl.addEventListener('shown.bs.modal', function () {
        createMap();
        if (editor.map) setTimeout(function () { editor.map.invalidateSize(); }, 80);
      });
    } else {
      createMap();
    }
  }

  return { init: init, _parseManualText: parseManualText };
})();