"""Generate static/main/svg/world-map.svg from world.geojson."""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / 'static/main/svg/world.geojson'
OUT = ROOT / 'static/main/svg/world-map.svg'
ISO_JSON = ROOT / 'static/main/json/iso2-iso3.json'
ISO_URL = (
    'https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/'
    'master/all/all.json'
)


def load_iso_maps():
    if ISO_JSON.exists():
        data = json.loads(ISO_JSON.read_text(encoding='utf-8'))
    else:
        with urllib.request.urlopen(ISO_URL, timeout=30) as resp:
            rows = json.loads(resp.read().decode('utf-8'))
        data = {r['alpha-2']: r['alpha-3'] for r in rows if r.get('alpha-2')}
        ISO_JSON.parent.mkdir(parents=True, exist_ok=True)
        ISO_JSON.write_text(json.dumps(data, indent=0), encoding='utf-8')
    iso3_to_iso2 = {v: k for k, v in data.items()}
    return data, iso3_to_iso2


def project(lon, lat):
    return (lon + 180) / 360 * 960, (90 - lat) / 180 * 480


def ring_path(ring):
    pts = []
    for lon, lat in ring:
        x, y = project(lon, lat)
        pts.append(f'{x:.1f},{y:.1f}')
    return 'M' + ' L'.join(pts) + ' Z'


def geom_paths(geom):
    t = geom['type']
    coords = geom['coordinates']
    if t == 'Polygon':
        return [ring_path(coords[0])]
    if t == 'MultiPolygon':
        return [ring_path(poly[0]) for poly in coords]
    return []


def main():
    iso2_to_iso3, iso3_to_iso2 = load_iso_maps()
    data = json.loads(GEOJSON.read_text(encoding='utf-8'))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 480" class="geo-map geo-map-svg" aria-hidden="true">',
        '<defs>',
        '<linearGradient id="geoMapBg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#0a0d14"/><stop offset="100%" stop-color="#05060a"/>',
        '</linearGradient>',
        '<filter id="geoGlow" x="-50%" y="-50%" width="200%" height="200%">',
        '<feGaussianBlur stdDeviation="2" result="blur"/>',
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '</filter>',
        '<style><![CDATA[',
        '.geo-country{fill:rgba(0,240,255,0.06);stroke:rgba(0,240,255,0.14);stroke-width:0.5;',
        'transition:fill .35s ease,stroke .35s ease,filter .35s ease}',
        '.geo-country--active{fill:rgba(0,240,255,calc(0.12 + 0.55 * var(--geo-intensity,0.5)));',
        'stroke:rgba(0,240,255,calc(0.35 + 0.45 * var(--geo-intensity,0.5)));stroke-width:0.75;',
        'filter:url(#geoGlow)}',
        ']]></style>',
        '</defs>',
        '<rect width="960" height="480" fill="url(#geoMapBg)"/>',
        '<g class="geo-map__grid" stroke="rgba(0,240,255,0.07)" stroke-width="1">',
        '<line x1="240" y1="0" x2="240" y2="480"/><line x1="480" y1="0" x2="480" y2="480"/>'
        '<line x1="720" y1="0" x2="720" y2="480"/>',
        '<line x1="0" y1="120" x2="960" y2="120"/><line x1="0" y1="240" x2="960" y2="240"/>'
        '<line x1="0" y1="360" x2="960" y2="360"/>',
        '</g>',
        '<g class="geo-map__countries">',
    ]
    count = 0
    for feat in data['features']:
        cid = feat.get('id') or ''
        if len(cid) != 3:
            continue
        iso2 = iso3_to_iso2.get(cid, '')
        for d in geom_paths(feat['geometry']):
            parts.append(
                f'<path id="{cid}" class="geo-country" data-iso3="{cid}" '
                f'data-iso2="{iso2}" d="{d}"/>'
            )
            count += 1
    parts.append('</g></svg>')
    OUT.write_text('\n'.join(parts), encoding='utf-8')
    print(f'Wrote {count} countries to {OUT}')


if __name__ == '__main__':
    main()
