// Lettore B: solo Node, nessuna libreria. Parser JSON + proiezione inversa UTM32N (serie di Krueger, GRS80)
// scritta qui: serve a verificare in modo indipendente da PROJ/GDAL. Uso: node leggi_node.js
const fs = require("fs"), path = require("path");
const fc = JSON.parse(fs.readFileSync(path.join(__dirname, "z2_campione.geojson"), "utf8"));
const a = 6378137, f = 1 / 298.257222101, k0 = 0.9996, E0 = 500000, lon0 = 9 * Math.PI / 180;
const n = f / (2 - f), A = a / (1 + n) * (1 + n*n/4 + n**4/64);
const be = [n/2 - 2*n*n/3 + 37*n**3/96, n*n/48 + n**3/15, 17*n**3/480];
const dl = [2*n - 2*n*n/3 - 2*n**3, 7*n*n/3 - 8*n**3/5, 56*n**3/15];
function inv(E, N) {
  const xi = N / (k0 * A), eta = (E - E0) / (k0 * A);
  let xp = xi, ep = eta;
  be.forEach((b, i) => { const j = 2*(i+1); xp -= b*Math.sin(j*xi)*Math.cosh(j*eta); ep -= b*Math.cos(j*xi)*Math.sinh(j*eta); });
  const chi = Math.asin(Math.sin(xp) / Math.cosh(ep));
  let phi = chi; dl.forEach((d, i) => { phi += d * Math.sin(2*(i+1)*chi); });
  const lam = lon0 + Math.atan2(Math.sinh(ep), Math.cos(xp));
  return [lam * 180 / Math.PI, phi * 180 / Math.PI];
}
const dist = (p, q) => Math.hypot(p[0]-q[0], p[1]-q[1]);
const len = c => c.slice(1).reduce((s, p, i) => s + dist(c[i], p), 0);
const area = r => Math.abs(r.slice(1).reduce((s, p, i) => s + r[i][0]*p[1] - p[0]*r[i][1], 0)) / 2;
const byl = {}, ids = {}; let bb = [1e12, 1e12, -1e12, -1e12], L = 0, Ar = 0, err = 0;
const up = p => { bb = [Math.min(bb[0], p[0]), Math.min(bb[1], p[1]), Math.max(bb[2], p[0]), Math.max(bb[3], p[1])]; };
for (const ft of fc.features) {
  const p = ft.properties, g = ft.geometry; byl[p.layer] = (byl[p.layer] || 0) + 1; ids[p.id] = g;
  const flat = g.type === "Point" ? [g.coordinates] : g.type === "LineString" ? g.coordinates : g.coordinates[0];
  flat.forEach(up);
  if (p.id.startsWith("way_")) L += len(g.coordinates);
  if (p.id.startsWith("bld_")) Ar += area(g.coordinates[0]);
  if (p.orig_wgs84) { const [lo, la] = inv(...g.coordinates); err = Math.max(err, Math.abs(lo - p.orig_wgs84[0]), Math.abs(la - p.orig_wgs84[1])); }
}
const s = ids["dst_school_piee82101p"].coordinates, pe = ids["dst_stop_pi4390"].coordinates, ll = inv(...s);
const r2 = v => Math.round(v * 100) / 100, r7 = v => Math.round(v * 1e7) / 1e7;
console.log(JSON.stringify({ reader: "node-stdlib", crs_declared: fc.crs.properties.name, counts: byl, bbox: bb.map(r2),
  network_length_m: r2(L), building_area_m2: r2(Ar), school_to_pellico_m: r2(dist(s, pe)),
  school_lonlat_node: [r7(ll[0]), r7(ll[1])], max_roundtrip_err_deg: err }, null, 1));
