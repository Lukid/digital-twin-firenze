"""D39: coordinate arrotondate prima di scrivere ogni GeoJSON o JSON con geometrie, così Mac e Linux scrivono gli stessi byte.
Le differenze di aritmetica fra le due macchine stanno oltre la 14ª cifra decimale: dopo l'arrotondamento spariscono.
Uso: from coordinate import arrotonda; json.dumps(arrotonda(fc)) con fc una geometria, una Feature o una FeatureCollection (anche mapping di shapely)."""

GRADI = 8   # EPSG:4326: 1e-8 gradi = circa 1 mm. I dati valgono al centimetro (1e-7); l'ottava cifra tiene identico al centimetro il ritorno 4326 -> 7791 dei ricevitori
METRI = 2   # EPSG:7791: centimetro


def _r(c, d):
    return round(c, d) if isinstance(c, float) else [_r(x, d) for x in c]


def arrotonda(o, decimali=GRADI):
    """Copia di `o` con tutte le "coordinates" arrotondate a `decimali` (tuple diventano liste). Le proprietà non cambiano."""
    if isinstance(o, dict):
        return {k: (_r(v, decimali) if k == "coordinates" else arrotonda(v, decimali)) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [arrotonda(x, decimali) for x in o]
    return o


if __name__ == "__main__":   # verifica: python pipeline/coordinate.py
    g = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": ((11.226574043148673, 43.79070053927385), (11.2, 43.7))}, "properties": {"h": 1.23456789}}
    assert arrotonda(g)["geometry"]["coordinates"] == [[11.22657404, 43.79070054], [11.2, 43.7]] and arrotonda(g)["properties"]["h"] == 1.23456789
    assert arrotonda({"coordinates": [1234.5678, 5.0]}, METRI) == {"coordinates": [1234.57, 5.0]}
    print("ok")
