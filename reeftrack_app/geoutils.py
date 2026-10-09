import json
from decimal import Decimal, InvalidOperation


def parse_decimal(value, label):
    """Parse a numeric string. Raises ValueError with a friendly message."""
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f'{label} must be a valid number.')


def parse_geometry_file(f):
    """Parse an uploaded GeoJSON file.

    Returns (boundary_geometry, lat, lng). `lat`/`lng` are the bounding-box
    center of the geometry (floats), or None if the geometry has no
    coordinates. Raises ValueError with a friendly message on bad input.
    """
    try:
        raw = f.read().decode('utf-8-sig')
    except Exception:
        raise ValueError('The uploaded file could not be read as text.')
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError('The uploaded file is not valid JSON/GeoJSON.')
    geom = polygonize(data)
    if geom is None:
        geom = extract_geometry(data)
    try:
        for _ in _iter_points(geom):
            pass
    except ValueError as exc:
        raise ValueError(str(exc))
    lat, lng = centroid_of(geom)
    return geom, lat, lng


def polygonize(data):
    """Collect every polygonal ring from a GeoJSON object into one geometry.

    Handles bare geometries, `Feature`, `FeatureCollection` and
    `GeometryCollection`, merging all Polygon/MultiPolygon parts into a single
    Polygon (one part) or MultiPolygon (many parts). Non-polygonal features
    (Points/Lines) are ignored. Returns None when no polygon is present.
    """
    if not isinstance(data, dict):
        return None

    parts = []

    def collect(geom):
        if not isinstance(geom, dict):
            return
        t = geom.get('type')
        if t == 'Polygon':
            coords = geom.get('coordinates') or []
            if coords:
                parts.append(coords)
        elif t == 'MultiPolygon':
            for poly in geom.get('coordinates') or []:
                if poly:
                    parts.append(poly)
        elif t == 'GeometryCollection':
            for sub in geom.get('geometries') or geom.get('coordinates') or []:
                collect(sub)

    top = data.get('type')
    if top == 'FeatureCollection':
        for feat in data.get('features') or []:
            if isinstance(feat, dict):
                collect(feat.get('geometry'))
    elif top == 'Feature':
        collect(data.get('geometry'))
    else:
        collect(data)

    if not parts:
        return None
    if len(parts) == 1:
        return {'type': 'Polygon', 'coordinates': parts[0]}
    return {'type': 'MultiPolygon', 'coordinates': parts}



def parse_manual_polygon(raw):
    """Parse a boundary sourced from the admin form (drawn on the map).

    Accepts a JSON string that is either a GeoJSON Polygon/MultiPolygon
    geometry object, or a bare list of rings (each ring a list of [lng, lat]
    coordinates). Returns a Polygon or MultiPolygon geometry dict. Rings are
    validated and auto-closed. Raises ValueError with a friendly message.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise ValueError('Coordinates must be valid JSON.')
    if isinstance(data, dict):
        geom = polygonize(data)
        if geom is None:
            raise ValueError('Boundary must be a Polygon or MultiPolygon.')
        for _ in _iter_points(geom):
            pass
        return geom
    if not isinstance(data, list) or not data:
        raise ValueError('Boundary must contain at least one ring.')
    rings = []
    for ring in data:
        if not isinstance(ring, list) or len(ring) < 3:
            raise ValueError('Each boundary ring needs at least 3 coordinate points.')
        coords = []
        for coord in ring:
            lat, lng = _point(coord)
            coords.append([lng, lat])
        if coords[0] != coords[-1]:
            coords.append(list(coords[0]))
        rings.append(coords)
    if len(rings) == 1:
        return {'type': 'Polygon', 'coordinates': rings}
    return {'type': 'MultiPolygon', 'coordinates': [[r] for r in rings]}


def extract_geometry(data):
    """Reduce a GeoJSON object to a single geometry (first feature if a collection)."""
    if not isinstance(data, dict):
        raise ValueError('GeoJSON must be a JSON object.')
    t = data.get('type')
    if t == 'FeatureCollection':
        features = data.get('features') or []
        if not features:
            raise ValueError('The GeoJSON FeatureCollection contains no features.')
        return extract_geometry(features[0])
    if t == 'Feature':
        g = data.get('geometry')
        if not g:
            raise ValueError('The GeoJSON Feature has no geometry.')
        return extract_geometry(g)
    if t in ('Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection'):
        if 'coordinates' not in data and t != 'GeometryCollection':
            raise ValueError(f'GeoJSON {t} is missing coordinates.')
        return data
    raise ValueError('Unsupported GeoJSON type. Use a Polygon, MultiPolygon, or Point.')


def _point(coord):
    if not isinstance(coord, (list, tuple)) or len(coord) < 2:
        raise ValueError('GeoJSON coordinate is invalid.')
    try:
        lng = float(coord[0])
        lat = float(coord[1])
    except (TypeError, ValueError):
        raise ValueError('GeoJSON coordinates must be numbers.')
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise ValueError('GeoJSON coordinates are out of range.')
    return lat, lng


def _iter_points(geom):
    t = geom.get('type')
    coords = geom.get('coordinates')
    if t == 'Point':
        yield _point(coords)
    elif t in ('MultiPoint', 'LineString'):
        for c in coords:
            yield _point(c)
    elif t == 'MultiLineString':
        for line in coords:
            for c in line:
                yield _point(c)
    elif t == 'Polygon':
        for ring in coords:
            for c in ring:
                yield _point(c)
    elif t == 'MultiPolygon':
        for poly in coords:
            for ring in poly:
                for c in ring:
                    yield _point(c)
    elif t == 'GeometryCollection':
        for g in coords:
            for p in _iter_points(g):
                yield p
    else:
        raise ValueError('Unsupported GeoJSON type.')


def centroid_of(geom):
    """Bounding-box center of a geometry (in lat/lng order)."""
    pts = list(_iter_points(geom))
    if not pts:
        return None, None
    lats = [p[0] for p in pts]
    lngs = [p[1] for p in pts]
    return round((min(lats) + max(lats)) / 2, 6), round((min(lngs) + max(lngs)) / 2, 6)