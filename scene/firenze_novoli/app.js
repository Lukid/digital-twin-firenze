import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const $ = (id) => document.getElementById(id);
const stato = (t) => { $('stato').textContent = t; };

// --- asset: gzip + sha256 verificato ---------------------------------------
async function carica(idx, nome) {
  const m = idx.assets[nome];
  const buf = await (await fetch('assets/' + m.file)).arrayBuffer();
  if (buf.byteLength !== m.byte) throw new Error(`${m.file}: dimensione diversa dall'indice`);
  if (crypto.subtle) {
    const h = [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map((b) => b.toString(16).padStart(2, '0')).join('');
    if (h !== m.sha256) throw new Error(`${m.file}: sha256 diverso dall'indice`);
  }
  return new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
}
const f32 = (b64) => { const s = atob(b64), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return new Float32Array(u.buffer); };

// --- sole (algoritmo astronomico semplificato, precisione di circa 0,1 gradi) ----
const RAD = Math.PI / 180;
function sunPos(ms, lat, lon) {
  const d = ms / 864e5 - 10957.5, M = RAD * (357.5291 + 0.98560028 * d);
  const C = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
  const L = M + C + RAD * 102.9372 + Math.PI, e = RAD * 23.4397;
  const dec = Math.asin(Math.sin(e) * Math.sin(L)), ra = Math.atan2(Math.sin(L) * Math.cos(e), Math.cos(L));
  const H = RAD * (280.16 + 360.9856235 * d) + RAD * lon - ra, phi = RAD * lat;
  const alt = Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
  const az = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi)) + Math.PI; // da nord, orario
  return { alt, az };
}
const romeFmt = new Intl.DateTimeFormat('en-US', { timeZone: 'Europe/Rome', hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' });
function romeOffset(ms) { const p = Object.fromEntries(romeFmt.formatToParts(ms).map((x) => [x.type, +x.value])); return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - Math.floor(ms / 6e4) * 6e4; }
function romeToUtc(y, mo, d, h, mi) { const l = Date.UTC(y, mo - 1, d, h, mi); let u = l - romeOffset(l); u = l - romeOffset(u); return u; }
const PUNTI = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest'];

// --- mappa di base: verde, acqua e strade OSM dipinti in una texture del terreno ----
const MAPPA = { fondo: '#ece6d8', verde: '#cfdeb0', acqua: '#a9cbe3', strada: '#d3d6da', bordo: '#c2c1bb', cammino: '#ddd5c4' };
function mappaBase(M, x0, z0, W, H) {
  const N = matchMedia('(pointer:coarse)').matches || innerWidth < 700 ? 2048 : 4096, k = N / Math.max(W, H);
  const c = document.createElement('canvas'); c.width = Math.round(W * k); c.height = Math.round(H * k);
  const x = c.getContext('2d'), px = (v) => (v - x0) * k, pz = (v) => (v - z0) * k;
  x.fillStyle = MAPPA.fondo; x.fillRect(0, 0, c.width, c.height);
  const aree = (lista, col) => {
    x.fillStyle = col;
    for (const anelli of lista) { x.beginPath(); for (const r of anelli) { for (let i = 0; i < r.length; i += 2) (i ? x.lineTo : x.moveTo).call(x, px(r[i]), pz(r[i + 1])); x.closePath(); } x.fill('evenodd'); }
  };
  aree(M.verde, MAPPA.verde); aree(M.acqua, MAPPA.acqua);
  x.lineCap = x.lineJoin = 'round';
  const linee = (filtro, col, piu) => {
    x.strokeStyle = col;
    for (const s of M.strade.filter(filtro)) { x.lineWidth = (s.w + piu) * k; x.beginPath(); for (let i = 0; i < s.p.length; i += 2) (i ? x.lineTo : x.moveTo).call(x, px(s.p[i]), pz(s.p[i + 1])); x.stroke(); }
  };
  linee((s) => s.c, MAPPA.cammino, 0);
  linee((s) => !s.c, MAPPA.bordo, 1.5); linee((s) => !s.c, MAPPA.strada, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
// tono stabile per edificio, dall'id: variazione leggera come nei tetti veri
const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return ((h >>> 0) % 1000) / 1000; };

// --- avvio -------------------------------------------------------------------
async function main() {
  const idx = await (await fetch('assets/index.json')).json();
  const [LON, LAT] = idx.area.lon_lat_centro;
  const [A, B] = idx.area.semiassi_m;
  const dati = {};
  for (const k of Object.keys(idx.assets)) dati[k] = await carica(idx, k);

  const canvas = $('tela');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = false;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(50, 1, 5, 9000);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.maxPolarAngle = 1.5; controls.minDistance = 30; controls.maxDistance = 3500;
  controls.listenToKeyEvents(canvas);
  const VISTA = { pos: new THREE.Vector3(-350, 750, 1250), tgt: new THREE.Vector3(0, 0, 0) };
  const vai = (p, t) => { camera.position.copy(p); controls.target.copy(t); controls.update(); dirty = true; };

  const hemi = new THREE.HemisphereLight(0xeef3f8, 0xb6a68c, 0.9); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xfff1d6, 2.6);
  const SM = matchMedia('(pointer:coarse)').matches || innerWidth < 700 ? 2048 : 4096;
  sun.castShadow = true; sun.shadow.mapSize.set(SM, SM); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.7;
  const sc = sun.shadow.camera; const R = Math.hypot(A, B) + 120; sc.left = -R; sc.right = R; sc.top = R; sc.bottom = -R; sc.near = 50; sc.far = 4500; sc.updateProjectionMatrix();
  scene.add(sun, sun.target);

  const gruppi = {};   // livello -> Object3D
  const sel = [];      // oggetti selezionabili (mesh)
  let dirty = true, shadowDirty = true;

  // terreno
  const T = dati.terreno;
  const tY = (x, z) => {
    const fx = Math.min(Math.max((x - T.x0) / T.passo, 0), T.nx - 1.001), fz = Math.min(Math.max((z - T.z0) / T.passo, 0), T.ny - 1.001);
    const i = Math.floor(fx), j = Math.floor(fz), u = fx - i, v = fz - j, q = (a, b) => T.quote_cm[b * T.nx + a] / 100;
    return (q(i, j) * (1 - u) + q(i + 1, j) * u) * (1 - v) + (q(i, j + 1) * (1 - u) + q(i + 1, j + 1) * u) * v;
  };
  {
    const p = new Float32Array(T.nx * T.ny * 3), ix = [];
    for (let j = 0; j < T.ny; j++) for (let i = 0; i < T.nx; i++) { const k = (j * T.nx + i) * 3; p[k] = T.x0 + i * T.passo; p[k + 1] = T.quote_cm[j * T.nx + i] / 100; p[k + 2] = T.z0 + j * T.passo; }
    for (let j = 0; j < T.ny - 1; j++) for (let i = 0; i < T.nx - 1; i++) { const a = j * T.nx + i, b = a + 1, c = a + T.nx, d = c + 1; ix.push(a, c, b, b, c, d); }
    const W = (T.nx - 1) * T.passo, H = (T.ny - 1) * T.passo, uv = new Float32Array(T.nx * T.ny * 2);
    for (let k = 0; k < T.nx * T.ny; k++) { uv[k * 2] = (p[k * 3] - T.x0) / W; uv[k * 2 + 1] = 1 - (p[k * 3 + 2] - T.z0) / H; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setIndex(ix); g.computeVertexNormals();
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: mappaBase(dati.mappa, T.x0, T.z0, W, H), roughness: 1 })); m.receiveShadow = true;
    // piano di fondo oltre il riquadro, dello stesso colore: il bordo sfuma nella foschia
    const fondoPiano = new THREE.Mesh(new THREE.PlaneGeometry(20000, 20000).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: MAPPA.fondo, roughness: 1 }));
    fondoPiano.position.y = Math.min(...T.quote_cm) / 100 - 1.5; m.add(fondoPiano);
    gruppi.terreno = m; scene.add(m);
  }

  // edifici
  const COL = { measured: 0xc0643c, derived: 0xd98d62, assente: 0x7d828a }, MURO = new THREE.Color(0xf1e6d6);
  let edMesh, edStart = [];
  {
    const E = dati.edifici, pos = f32(E.posizioni), col = new Float32Array(pos.length), c = new THREE.Color(), w = new THREE.Color();
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.computeVertexNormals();
    const nor = g.attributes.normal.array;
    let v = 0;
    for (const e of E.edifici) {
      edStart.push(v); c.set(e.presente_2023 ? COL[e.classe_h] : COL.assente);
      if (e.presente_2023) c.offsetHSL((hash(e.id) - 0.5) * 0.03, 0, (hash(e.id + 'l') - 0.5) * 0.1);
      w.copy(c).lerp(MURO, 0.6);
      for (let i = v; i < v + e.n; i++) { const q = nor[i * 3 + 1] > 0.5 ? c : w; col.set([q.r, q.g, q.b], i * 3); }   // tetto se la normale guarda in alto
      v += e.n;
    }
    edStart.push(v);
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    edMesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 }));
    edMesh.castShadow = edMesh.receiveShadow = true; gruppi.edifici = edMesh; scene.add(edMesh);
  }

  // alberi (istanze)
  let chiome, tronchi;
  {
    const AL = dati.alberi.alberi, n = AL.length, m = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
    chiome = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ roughness: 1, flatShading: true }), n);
    tronchi = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 1, 6), new THREE.MeshStandardMaterial({ color: 0x6b4a2f, roughness: 1 }), n);
    AL.forEach((a, i) => {
      const imp = Math.min(a.imp ?? 1, a.h * 0.8), hc = Math.max(a.h - imp, 0.5), d = a.d ?? 3.5, r = Math.max(a.td ?? 0.1, 0.25) / 2;
      m.compose(new THREE.Vector3(a.x, a.y + imp + hc / 2, a.z), q, new THREE.Vector3(d / 2, hc / 2, d / 2)); chiome.setMatrixAt(i, m);
      c.set(a.ch_cls === 'estimated' ? 0x9cbf74 : 0x55894a); chiome.setColorAt(i, c);
      m.compose(new THREE.Vector3(a.x, a.y + imp / 2, a.z), q, new THREE.Vector3(r, imp, r)); tronchi.setMatrixAt(i, m);
    });
    chiome.castShadow = tronchi.castShadow = true; chiome.receiveShadow = true;
    const g = new THREE.Group(); g.add(chiome, tronchi); gruppi.alberi = g; scene.add(g);
  }

  // nastri sul terreno
  const hex = (n) => new THREE.Color(n);
  function nastri(tratti, yoff, lar, colore) {
    const P = [], C = [];
    for (const t of tratti) {
      const w = lar(t), col = colore(t), p = t.p;
      for (let k = 0; k + 3 < p.length; k += 2) {
        const dx = p[k + 2] - p[k], dz = p[k + 3] - p[k + 1], L = Math.hypot(dx, dz) || 1, n = Math.ceil(L / 8);
        const px = (-dz / L) * w / 2, pz = (dx / L) * w / 2;
        for (let s = 0; s < n; s++) {
          const x1 = p[k] + dx * s / n, z1 = p[k + 1] + dz * s / n, x2 = p[k] + dx * (s + 1) / n, z2 = p[k + 1] + dz * (s + 1) / n;
          const y1 = tY(x1, z1) + yoff, y2 = tY(x2, z2) + yoff;
          P.push(x1 - px, y1, z1 - pz, x1 + px, y1, z1 + pz, x2 - px, y2, z2 - pz, x1 + px, y1, z1 + pz, x2 + px, y2, z2 + pz, x2 - px, y2, z2 - pz);
          for (let v = 0; v < 6; v++) C.push(col.r, col.g, col.b);
        }
      }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3)); g.computeVertexNormals();
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
    m.receiveShadow = true; return m;
  }
  const RC = { strada: [0x5b6470, 5], sentiero: [0xb0763a, 2.2], marciapiede_disegnato: [0x2f6fb5, 2.2], attraversamento: [0xf2f2f2, 3.2] };
  gruppi.rete = nastri(dati.rete.archi, 0.2, (t) => (RC[t.tipo] || [0, 2.6])[1], (t) => hex((RC[t.tipo] || [0x8e44ad])[0]));
  scene.add(gruppi.rete);

  // punti: destinazioni, tram, scuole, rifugi, aree di protezione civile, barriere
  const PUNTO = { destinazioni: [0xd9480f, 5, 14], tram: [0x00a8e8, 6, 26], scuole: [0x7048e8, 6, 26], rifugi: [0x2f9e44, 6, 22], attesa: [0x1864ab, 6, 26], assistenza: [0xe67700, 6, 26], barriere: [0xc2255c, 1.6, 5] };
  // icone: cerchio col colore del livello e una sigla (T tram, S scuola, R rifugio climatico, AT e AA aree di attesa e di assistenza come nei codici del Comune)
  const ICONE = {};
  for (const [k, l] of [['tram', 'T'], ['scuole', 'S'], ['rifugi', 'R'], ['attesa', 'AT'], ['assistenza', 'AA']]) {
    const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
    x.beginPath(); x.arc(32, 32, 29, 0, 7); x.fillStyle = '#' + PUNTO[k][0].toString(16).padStart(6, '0'); x.fill(); x.lineWidth = 4; x.strokeStyle = '#fff'; x.stroke();
    x.fillStyle = '#fff'; x.font = `bold ${l.length > 1 ? 28 : 40}px system-ui, sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(l, 32, 35);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; ICONE[k] = { url: c.toDataURL(), t };
  }
  const sfera = new THREE.SphereGeometry(1, 12, 8), palo = new THREE.CylinderGeometry(0.25, 0.25, 1, 6);
  for (const k of Object.keys(PUNTO)) { gruppi[k] = new THREE.Group(); scene.add(gruppi[k]); }
  for (const p of dati.punti.punti) {
    if (p.fuori) continue;   // oltre il terreno disegnato: elenco sotto il livello, come le stazioni ARPAT
    const [col, r, h] = PUNTO[p.livello], g = gruppi[p.livello], q = new THREE.Group();
    const ic = ICONE[p.livello], m = ic ? new THREE.Sprite(new THREE.SpriteMaterial({ map: ic.t })) : new THREE.Mesh(sfera, new THREE.MeshStandardMaterial({ color: col, roughness: 0.6 }));
    m.scale.setScalar(ic ? 3 * r : r); m.position.y = h; m.userData = { tipo: p.livello, punto: p }; q.add(m); sel.push(m);
    const s = new THREE.Mesh(palo, m.isSprite ? new THREE.MeshStandardMaterial({ color: col }) : m.material); s.scale.y = h; s.position.y = h / 2; q.add(s);
    q.position.set(p.x, tY(p.x, p.z), p.z); g.add(q);
    if (p.contorno) g.add(nastri([{ p: p.contorno }], 0.4, () => 2, () => hex(col)));
  }

  // nomi dei luoghi: testo HTML posizionato sulla proiezione del punto, senza sovrapposizioni
  const etiq = { visible: true, el: $('etichette'), voci: [] }; gruppi.etichette = etiq;
  for (const e of dati.etichette.etichette) {
    const d = document.createElement('span'); d.className = e.k === 1 ? 'luogo' : 'via'; d.textContent = e.t; etiq.el.appendChild(d);
    etiq.voci.push({ d, k: e.k, p: new THREE.Vector3(e.x, tY(e.x, e.z) + (e.k === 1 ? 30 : 4), e.z) });
  }
  const pr = new THREE.Vector3();
  function posaEtichette() {
    etiq.el.hidden = !etiq.visible; if (!etiq.visible) return;
    const W = innerWidth, H = innerHeight, presi = [];
    for (const v of etiq.voci) {
      if (v.cat && !gruppi.catasto?.visible) { v.d.style.visibility = 'hidden'; continue; }
      pr.copy(v.p).project(camera);
      const lontano = camera.position.distanceTo(v.p) > (v.k === 1 ? 3200 : 1400);
      const x = (pr.x + 1) / 2 * W, y = (1 - pr.y) / 2 * H, w = v.d.offsetWidth, h = v.d.offsetHeight;
      const r = [x - w / 2, y - h / 2, x + w / 2, y + h / 2];
      const ok = pr.z < 1 && !lontano && x > 0 && x < W && y > 0 && y < H && !presi.some((q) => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1]);
      v.d.style.visibility = ok ? 'visible' : 'hidden';
      if (ok) { presi.push(r); v.d.style.transform = `translate(${(x - w / 2).toFixed(1)}px,${(y - h / 2).toFixed(1)}px)`; }
    }
  }

  // catasto: confini di particelle e fogli dipinti sul terreno, numero del foglio come etichetta
  const COL_CAT = 0x8a5a2b, COL_FOGLIO = 0x5c3a1a, catSel = new THREE.Group();
  const anelli = (a) => a.flatMap((poly) => poly.map((r) => ({ p: [...r, r[0], r[1]] })));   // anelli chiusi come tratti
  if (dati.catasto) {
    const C = dati.catasto, g = new THREE.Group();
    g.add(nastri(C.particelle.flatMap((q) => anelli(q.a)), 0.25, () => 0.5, () => hex(COL_CAT)));
    g.add(nastri(C.fogli.flatMap((q) => anelli(q.a)), 0.3, () => 1.6, () => hex(COL_FOGLIO)));
    g.add(catSel); gruppi.catasto = g; scene.add(g);
    for (const f of C.fogli) {
      const d = document.createElement('span'); d.className = 'foglio'; d.textContent = 'Foglio ' + f.f; etiq.el.appendChild(d);
      etiq.voci.push({ d, k: 2, cat: true, p: new THREE.Vector3(f.x, tY(f.x, f.z) + 2, f.z) });
    }
  }

  // temperatura delle superfici (Landsat): griglia a 30 m dipinta su una copia del terreno, semitrasparente
  const RAMPA = [[20, '#2c7bb6'], [30, '#abd9e9'], [35, '#ffffbf'], [40, '#fdae61'], [50, '#d7191c']];
  const coloreT = (t) => { let k = 1; while (k < RAMPA.length - 1 && t > RAMPA[k][0]) k++; const [t0, a] = RAMPA[k - 1], [t1, b] = RAMPA[k]; return new THREE.Color(a).lerp(new THREE.Color(b), Math.min(Math.max((t - t0) / (t1 - t0), 0), 1)); };
  let tMesh = null, tVista = 'media';
  const TM = dati.temperature;
  function mostraTemperatura(vista) {
    tVista = vista;
    const c = document.createElement('canvas'); c.width = TM.nx; c.height = TM.ny;
    const x = c.getContext('2d'), im = x.createImageData(TM.nx, TM.ny);
    const v = vista === 'media' ? TM.media : vista === 'sopra_40' ? TM.sopra_40 : TM.date[+vista].t, maxN = Math.max(1, ...TM.sopra_40);
    v.forEach((q, i) => {
      if (vista !== 'sopra_40' && q === TM.nodata) return;   // trasparente: dato non valido
      if (vista === 'sopra_40' && !TM.validi_per_cella[i]) return;
      const col = vista === 'sopra_40' ? new THREE.Color('#fff7ec').lerp(new THREE.Color('#7f0000'), q / maxN) : coloreT(q / 10);
      im.data.set([col.r * 255, col.g * 255, col.b * 255, 255], i * 4);
    });
    x.putImageData(im, 0, 0);
    const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
    if (!tMesh) {
      const g = gruppi.terreno.geometry.clone(), P = g.attributes.position.array, uv = g.attributes.uv.array;
      const gx = TM.x0 - TM.passo / 2, gz = TM.z0 - TM.passo / 2, W = TM.nx * TM.passo, H = TM.ny * TM.passo;
      for (let k = 0; k < P.length / 3; k++) { uv[k * 2] = (P[k * 3] - gx) / W; uv[k * 2 + 1] = 1 - (P[k * 3 + 2] - gz) / H; }
      tMesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.78, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
      tMesh.position.y = 0.4; tMesh.renderOrder = 5; tMesh.visible = false; gruppi.temperature = tMesh; scene.add(tMesh);
    }
    tMesh.material.map?.dispose(); tMesh.material.map = t; tMesh.material.needsUpdate = true;
    // aria alla stazione SIR nello stesso giorno, per confronto
    const M = dati.meteo, d = TM.date[+vista];
    const aria = M && d ? M.giorni.find((g) => g[0] === d.data) : null;
    $('leg_temperature').innerHTML = (vista === 'sopra_40'
      ? `<span>Quante delle ${TM.n} giornate estive sono sopra 40 °C in quella cella (da 0 a ${maxN}).</span><span><i style="background:linear-gradient(90deg,#fff7ec,#7f0000);width:120px"></i></span>`
      : `<span><i style="background:linear-gradient(90deg,${RAMPA.map((r) => r[1]).join(',')});width:120px"></i>da 20 a 50 °C</span>`)
      + (d ? `<span>${d.satellite}, ore ${d.ora_utc} UTC, ${d.validi_pct}% di celle valide.</span>` : vista === 'media' ? `<span>Media delle ${TM.n} giornate estive serene dal ${TM.date[0].data} al ${TM.date[TM.n - 1].data}.</span>` : '')
      + (aria ? `<span>Aria quel giorno, stazione ${tx(M.stazione.nome)} (a ${(M.stazione.distanza_fp_m / 1000).toFixed(1).replace('.', ',')} km): massima ${(aria[1] / 10).toFixed(1).replace('.', ',')} °C, minima ${(aria[2] / 10).toFixed(1).replace('.', ',')} °C.</span>` : '')
      + '<span>Tocca il terreno per leggere una cella. Le celle trasparenti non sono valide (nubi o acqua).</span>';
    shadowDirty = dirty = true;
  }

  // livelli analitici (vuoti se i dati non ci sono)
  const SCALA = [[5, '#fde725', 'fino a 5 min'], [10, '#35b779', '5-10 min'], [15, '#31688e', '10-15 min'], [1e9, '#440154', 'oltre 15 min']];
  const tex = (anello) => { const c = document.createElement('canvas'); c.width = c.height = 32; const x = c.getContext('2d'); x.beginPath(); x.arc(16, 16, 13, 0, 7); if (anello) { x.lineWidth = 4; x.strokeStyle = '#fff'; x.stroke(); } else { x.fillStyle = '#fff'; x.fill(); x.lineWidth = 3; x.strokeStyle = '#000'; x.stroke(); } return new THREE.CanvasTexture(c); };
  const T_PIENO = tex(false), T_ANELLO = tex(true);
  let accGruppo = null;
  function mostraAccessibilita(i) {
    if (accGruppo) { scene.remove(accGruppo); accGruppo.traverse((o) => o.geometry?.dispose()); }
    accGruppo = new THREE.Group();
    const d = dati.accessibilita.destinazioni[i], ok = [], co = [], no = [];
    for (const p of d.punti) {
      const y = tY(p.x, p.z) + 3;
      if (p.stato === 'ok' && p.min != null) { ok.push(p.x, y, p.z); const k = SCALA.find((s) => p.min <= s[0])[1]; const c = new THREE.Color(k); co.push(c.r, c.g, c.b); } else no.push(p.x, y, p.z);
    }
    const mk = (pos, colors, tx, size, col) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); if (colors) g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3)); const m = new THREE.Points(g, new THREE.PointsMaterial({ size, sizeAttenuation: false, map: tx, alphaTest: 0.4, vertexColors: !!colors, color: col || 0xffffff, depthTest: false })); m.renderOrder = 10; return m; };
    accGruppo.add(mk(ok, co, T_PIENO, 9), mk(no, null, T_ANELLO, 8, 0x777777));
    accGruppo.visible = $('l_accessibilita').checked; scene.add(accGruppo); gruppi.accessibilita = accGruppo;
    $('leg_accessibilita').innerHTML = '<span>Ogni pallino è un civico. Il colore indica i minuti a piedi da quel civico alla destinazione scelta.</span>' + SCALA.map((s) => `<span><i style="background:${s[1]}"></i>${s[2]}</span>`).join('') + '<span><i style="background:#fff;border:3px double #777;border-radius:50%"></i>non raggiungibile, vietato o dati insufficienti</span>' + `<span>${d.punti.filter((p) => p.stato === 'ok').length} civici su ${d.punti.length} arrivano alla destinazione${d.profilo ? ', profilo ' + d.profilo : ''}</span>`;
    dirty = true;
  }
  let ombraGruppo = null;
  function mostraOmbra(i) {
    if (ombraGruppo) { scene.remove(ombraGruppo); ombraGruppo.traverse((o) => o.geometry?.dispose()); }
    const c0 = hex(0xf2c230), c1 = hex(0x1b2a6b), I = dati.ombra.istanti[i], P = dati.ombra.percorsi || [];
    ombraGruppo = new THREE.Group();
    ombraGruppo.add(nastri(P, 0.5, () => 4, () => c0), nastri(I.tratti, 0.7, () => 4, (t) => c0.clone().lerp(c1, t.f ?? 0)));
    ombraGruppo.visible = $('l_ombra').checked; scene.add(ombraGruppo); gruppi.ombra = ombraGruppo; dirty = true;
    const pc = P.map((q) => `<span>${q.id.replace('pth_fi_', '')}: ${Math.round((I.quota?.[q.id] ?? 0) * 100)}% in ombra</span>`).join('');
    $('leg_ombra').innerHTML = pc + '<span>Il livello mostra l\'istante scelto, non segue il cursore dell\'ora.</span>';
  }

  // scenari: interventi ipotetici (livello spento all'avvio)
  const COL_SCN = 0xe0218a;
  let scnGruppo = null, scnCentro = null, scnL = 80, scnPick = [];
  function mostraScenario(i) {
    if (scnGruppo) { scene.remove(scnGruppo); scnGruppo.traverse((o) => o.geometry?.dispose()); }
    const S = dati.interventi.scenari[i], g = new THREE.Group(), m = new THREE.Matrix4(), q = new THREE.Quaternion();
    scnPick = []; let sx = 0, sz = 0, n = 0; const bb = new THREE.Box3();
    if (S.alberi.length) {
      const cr = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: COL_SCN, roughness: 1, flatShading: true }), S.alberi.length);
      const tr = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 1, 8), new THREE.MeshStandardMaterial({ color: 0x7a1450, roughness: 1 }), S.alberi.length);
      S.alberi.forEach((a, k) => {
        const y = tY(a.x, a.z), hc = a.h - a.imp;
        m.compose(new THREE.Vector3(a.x, y + a.imp + hc / 2, a.z), q, new THREE.Vector3(a.d / 2, hc / 2, a.d / 2)); cr.setMatrixAt(k, m);
        m.compose(new THREE.Vector3(a.x, y + a.imp / 2, a.z), q, new THREE.Vector3(0.2, a.imp, 0.2)); tr.setMatrixAt(k, m);
        sx += a.x; sz += a.z; n++; bb.expandByPoint(new THREE.Vector3(a.x, 0, a.z));
      });
      cr.castShadow = tr.castShadow = cr.receiveShadow = true; cr.userData = { scn: S, alberi: true }; g.add(cr, tr); scnPick.push(cr);
    }
    for (const p of S.pensiline) {
      const sh = new THREE.Shape(); for (let k = 0; k < p.p.length; k += 2) (k ? sh.lineTo : sh.moveTo).call(sh, p.p[k], -p.p[k + 1]);
      const cx = p.p.filter((_, k) => k % 2 === 0).reduce((a, b) => a + b) / (p.p.length / 2), cz = p.p.filter((_, k) => k % 2).reduce((a, b) => a + b) / (p.p.length / 2);
      const ge = new THREE.ExtrudeGeometry(sh, { depth: p.z_hi - p.z_lo, bevelEnabled: false }); ge.rotateX(-Math.PI / 2);
      const me = new THREE.Mesh(ge, new THREE.MeshStandardMaterial({ color: COL_SCN, roughness: 0.6 })); me.position.y = tY(cx, cz) + p.z_lo;
      me.castShadow = me.receiveShadow = true; me.userData = { scn: S, pens: p }; g.add(me); scnPick.push(me);
      // quattro pali fino a terra, per leggere la pensilina come struttura
      for (let k = 0; k < p.p.length; k += 2) { const pl = new THREE.Mesh(palo, me.material); const h = p.z_lo; pl.scale.set(1.4, h, 1.4); pl.position.set(p.p[k] * 0.92 + cx * 0.08, tY(cx, cz) + h / 2, p.p[k + 1] * 0.92 + cz * 0.08); pl.castShadow = true; g.add(pl); }
      sx += cx; sz += cz; n++; bb.expandByPoint(new THREE.Vector3(cx, 0, cz));
    }
    scnCentro = new THREE.Vector3(sx / n, 0, sz / n); scnCentro.y = tY(scnCentro.x, scnCentro.z); scnL = Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z, 120);
    g.visible = $('l_scenari').checked; scnGruppo = g; gruppi.scenari = g; scene.add(g); shadowDirty = dirty = true;
  }

  // --- pannello: righe dei livelli per sezione, come a Padova; i colori stanno nella scheda Legenda ----
  const tx = (v) => String(v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const ICO = {
    edifici: 'M4 21V8l6-4v17M10 21V10l10 3v8M3 21h18', alberi: 'M12 22v-6M7 11a5 5 0 1 1 10 0 5 5 0 0 1-10 0', terreno: 'M3 19l6-9 4 6 3-4 5 7z',
    etichette: 'M4 7h16M4 12h11M4 17h7', rete: 'M6 21c0-5 4-5 6-9s1-6 6-9', destinazioni: 'M12 3v4M12 17v4M3 12h4M17 12h4M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
    barriere: 'M4 8h16v5H4zM7 13v7M17 13v7M8 8l4 5M14 8l4 5', accessibilita: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3 2',
    ombra: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v2M12 20v2M2 12h2M20 12h2', scenari: 'M4 20l4-1 11-11-3-3L5 16zM14 7l3 3', catasto: 'M3 4h18v16H3zM3 11h9v9M12 4v7h9', temperature: 'M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0M12 9v8', altro: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
  };
  const TINTA = { edifici: '#c0643c', alberi: '#55894a', terreno: '#8a7a55', etichette: '#5d7f68', rete: '#2f6fb5', accessibilita: '#31688e', ombra: '#a87a00', scenari: '#e0218a', catasto: '#8a5a2b', temperature: '#d7191c' };
  const SEZIONE = { edifici: 'g_citta', alberi: 'g_citta', terreno: 'g_citta', etichette: 'g_citta', rete: 'g_mobilita', tram: 'g_mobilita', accessibilita: 'g_analisi', ombra: 'g_analisi', scenari: 'g_interventi', catasto: 'g_catasto', temperature: 'g_analisi' };
  const svg = (d) => `<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="${d}"/></svg>`;
  const css = (n) => '#' + n.toString(16).padStart(6, '0');
  const opzioni = (lista, et) => lista.map((d, i) => `<option value="${i}">${tx(d[et])}</option>`).join('');
  const SENZA_RIGA = ['meteo', 'aria'];   // dati senza oggetti in scena: stanno dentro altri livelli o nella scheda Analisi
  for (const [k, L] of Object.entries(idx.livelli)) {
    if (SENZA_RIGA.includes(k)) continue;
    const an = ['accessibilita', 'ombra', 'scenari'].includes(k), presente = an ? idx.livelli_analitici[k].presente : k !== 'temperature' || !!TM;
    const tinta = TINTA[k] || (PUNTO[k] ? css(PUNTO[k][0]) : '#5d7f68');
    const ico = ICONE[k] ? `<img src="${ICONE[k].url}" alt="" width="24" height="24">` : svg(ICO[k] || ICO.altro);
    const w = document.createElement('div');
    w.innerHTML = `<label class="liv"><span class="ico" style="color:${tinta};background:${tinta}1c">${ico}</span><span class="nome">${k === 'scenari' ? 'Mostra l\'intervento (dopo)' : L.etichetta}${presente ? '' : ' <em>(dati non presenti)</em>'}</span>`
      + `<span class="switch"><input type="checkbox" role="switch" id="l_${k}" ${presente ? '' : 'disabled'} ${!an && !['barriere', 'rete', 'catasto', 'temperature', 'aria'].includes(k) ? 'checked' : ''}><i></i></span></label>`;
    if (k === 'accessibilita' && presente) w.innerHTML += `<div class="sub"><label for="s_acc">Verso</label><select id="s_acc">${opzioni(dati.accessibilita.destinazioni, 'nome')}</select><div class="leg" id="leg_accessibilita"></div></div>`;
    if (k === 'ombra' && presente) w.innerHTML += `<div class="sub"><label for="s_om">Istante del calcolo</label><select id="s_om">${dati.ombra.istanti.map((d, i) => `<option value="${i}">${new Date(d.istante + ':00Z').toLocaleString('it-IT', { timeZone: 'UTC', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}</option>`).join('')}</select><div class="riga"><button type="button" id="vOm">Vai ai percorsi</button></div><div class="leg"><span>Due percorsi campione verso il Polo universitario.</span><span><i style="background:#f2c230"></i>al sole</span><span><i style="background:#1b2a6b"></i>in ombra</span></div><div class="leg" id="leg_ombra"></div></div>`;
    if (k === 'temperature' && TM) w.innerHTML += `<div class="sub"><label for="s_t">Cosa mostrare</label><select id="s_t"><option value="media">Media delle giornate estive</option><option value="sopra_40">Giornate sopra 40 °C</option>${TM.date.map((d, i) => `<option value="${i}">${new Date(d.data).toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: 'numeric' })}</option>`).join('')}</select><div class="leg" id="leg_temperature"></div></div>`;
    const lontani = dati.punti.punti.filter((p) => p.livello === k && p.fuori).sort((a, b) => a.distanza_m - b.distanza_m);
    if (lontani.length) w.innerHTML += `<div class="sub"><p class="intro">Fuori dal riquadro, quindi elenco e non punti in scena:</p>${lontani.map((p) => `<details class="staz"><summary><strong>${tx(p.nome)}</strong><small>a ${p.distanza_m} m dal riquadro</small></summary>`
      + `<ul>${Object.entries(p.attr).filter(([, v]) => v != null).map(([a, v]) => `<li><strong>${tx(a)}</strong>: ${tx(v)}</li>`).join('')}</ul></details>`).join('')}</div>`;
    $(SEZIONE[k] || 'g_luoghi').appendChild(w);
  }

  // scheda Interventi: uno scenario per riquadro, con i numeri del calcolo già visibili
  if (idx.livelli_analitici.scenari.presente) {
    const conta = (S) => [S.alberi.length && `${S.alberi.length} alberi`, S.pensiline.length && `${S.pensiline.length} pensilina`].filter(Boolean).join(', ');
    $('scnLista').innerHTML = dati.interventi.scenari.map((S, i) => `<label class="scn"><input type="radio" name="scn" value="${i}" ${i ? '' : 'checked'}><span><strong>${tx(S.etichetta)}</strong><small>${conta(S)}</small>`
      + `<dl>${S.numeri.map(([a, b]) => `<dt>${tx(a)}</dt><dd>${tx(b)}</dd>`).join('')}</dl></span></label>`).join('');
    $('scnFatt').textContent = 'Fattibilità ' + dati.interventi.scenari[0].fattibilita;
  } else $('p-interventi').querySelector('.intro').textContent = 'Nessuno scenario nei dati di questa scena.';

  // legenda: tutti i colori del modello in un posto solo
  const sw = (c, t) => `<span><i style="background:${c}"></i>${t}</span>`;
  const pin = (k, t) => `<span>${ICONE[k] ? `<img src="${ICONE[k].url}" alt="">` : `<i style="background:${css(PUNTO[k][0])};border-radius:50%"></i>`}${t}</span>`;
  $('legenda').innerHTML = [
    ['Edifici', sw('#d98d62', 'altezza dal rilievo laser 2023') + sw('#c0643c', 'altezza dai volumi del 2011') + sw('#7d828a', 'non presente nel 2023')],
    ['Alberi', sw('#55894a', 'chioma misurata dal rilievo laser') + sw('#9cbf74', 'chioma stimata')],
    ['Mappa di base (OpenStreetMap)', sw(MAPPA.verde, 'verde') + sw(MAPPA.acqua, 'acqua') + sw(MAPPA.strada, 'strade')],
    ['Rete pedonale', sw('#5b6470', 'strada') + sw('#b0763a', 'sentiero') + sw('#2f6fb5', 'marciapiede') + sw('#f2f2f2', 'attraversamento')],
    ['Segnaposto', pin('destinazioni', 'destinazione dei calcoli') + pin('tram', 'fermata del tram') + pin('scuole', 'scuola statale') + pin('rifugi', 'rifugio climatico') + pin('attesa', 'area di attesa') + pin('assistenza', 'area di assistenza') + pin('barriere', 'barriera architettonica')
      + '<span>Destinazioni: i 7 ingressi del Polo delle Scienze Sociali, le scuole Vamba (primaria e infanzia), le fermate T2 San Donato - Università, Regione Toscana e Torre degli Agli.</span>'],
    ['Accessibilità', SCALA.map((s) => sw(s[1], s[2])).join('') + '<span><i style="background:#fff;border:3px double #777;border-radius:50%"></i>non raggiungibile, vietato o dati insufficienti</span>'],
    ['Ombra sui percorsi', sw('#f2c230', 'al sole') + sw('#1b2a6b', 'in ombra')],
    ['Interventi', sw(css(COL_SCN), 'albero o pensilina ipotetici')],
    ['Temperatura delle superfici', `<span><i style="background:linear-gradient(90deg,${RAMPA.map((r) => r[1]).join(',')});width:120px"></i>da 20 a 50 °C</span>`],
    ['Catasto', sw(css(COL_CAT), 'confine di particella') + sw(css(COL_FOGLIO), 'confine di foglio') + sw('#ff7a1a', 'particella cercata')],
  ].map(([t, v]) => `<p class="sez">${t}</p><div class="leg">${v}</div>`).join('');

  // schede del pannello: frecce sinistra e destra per passare da una all'altra
  const tabs = [...document.querySelectorAll('.tabs [role=tab]')];
  const apri = (b) => { for (const t of tabs) { const on = t === b; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; $(t.getAttribute('aria-controls')).hidden = !on; } };
  tabs.forEach((b, i) => {
    b.addEventListener('click', () => apri(b));
    b.addEventListener('keydown', (e) => { const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key]; if (d) { const n = tabs[(i + d + tabs.length) % tabs.length]; apri(n); n.focus(); } });
  });

  for (const k of Object.keys(idx.livelli)) {
    const cb = $('l_' + k); if (!cb) continue;
    if (gruppi[k]) gruppi[k].visible = cb.checked;
    cb.addEventListener('change', () => { if (gruppi[k]) gruppi[k].visible = cb.checked; shadowDirty = dirty = true; });
  }
  // qualità dell'aria: stazioni ARPAT fuori dal riquadro, quindi elenco e non punti in scena
  if (dati.aria) {
    const A = dati.aria, n1 = (v) => v == null ? 'n.d.' : String(Math.round(v * 10) / 10).replace('.', ',');
    const riga = (q) => `<li><strong>${tx(q.parametro)}</strong>: media ${n1(q.media_annua)} ${tx(q.unita)}${q.limite_annuo ? ` (limite ${q.limite_annuo})` : ''}`
      + `${q.soglia ? `; ${q.superamenti} ${tx(q.conta)} sopra ${q.soglia} (ammessi ${q.ammessi ?? 0})` : ''}${q.copertura_ok ? '' : '; dati validi sotto il 90%, media non valida per la legge'}</li>`;
    $('aria').innerHTML = `<p class="intro">Valori di stazione del ${A.anno}, dati validati ARPAT. Nessuna stazione sta nel riquadro: sono le più vicine, non una mappa.</p>`
      + [...A.stazioni].sort((a, b) => a.distanza_m - b.distanza_m).map((st, i) => `<details class="staz"${i ? '' : ' open'}><summary><strong>${tx(st.codice)}</strong><small>${tx(st.tipo)}, a ${n1(st.distanza_m / 1000)} km dal riquadro</small></summary>`
        + `${st.avviso ? `<p class="avviso">${tx(st.avviso)}</p>` : ''}<ul>${st.inquinanti.map(riga).join('')}</ul></details>`).join('')
      + `<p class="intro">Limiti: D.Lgs. 155/2010. Fonte: ARPAT, archivio dei dati orari. Licenza dei dati orari non indicata; le note legali ARPAT dichiarano CC BY-NC-SA 3.0 IT per i contenuti del sito e CC BY 4.0 per le banche dati.</p>`;
  } else $('aria').closest('.blocco-aria').hidden = true;
  if (TM) { mostraTemperatura('media'); $('s_t').addEventListener('change', (e) => { mostraTemperatura(e.target.value); $('l_temperature').checked = true; $('l_temperature').dispatchEvent(new Event('change')); }); }
  if (dati.catasto) {
    $('catCerca').addEventListener('submit', (e) => {
      e.preventDefault();
      const f = $('catF').value.trim().toUpperCase(), n = $('catP').value.trim().toUpperCase();
      const q = dati.catasto.particelle.find((x) => x.p.toUpperCase() === n && (x.f.toUpperCase() === f || x.f.replace(/[A-Z]+$/, '') === f));
      catSel.traverse((o) => o.geometry?.dispose()); catSel.clear();
      if (!q) { $('catEsito').textContent = `Nessuna particella ${n} nel foglio ${f} dentro il riquadro.`; dirty = true; return; }
      catSel.add(nastri(anelli(q.a), 0.5, () => 2, () => hex(0xff7a1a)));
      const bb = new THREE.Box3(); for (const r of q.a[0]) for (let k = 0; k < r.length; k += 2) bb.expandByPoint(new THREE.Vector3(r[k], 0, r[k + 1]));
      const c = bb.getCenter(new THREE.Vector3()), L = Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z, 60); c.y = tY(c.x, c.z);
      $('l_catasto').checked = true; $('l_catasto').dispatchEvent(new Event('change'));
      vai(c.clone().add(new THREE.Vector3(0.2 * L, 2.2 * L, 0.8 * L)), c);
      $('catEsito').textContent = `Trovata: ${q.rif}${q.t !== 'particella' ? ' (' + q.t + ')' : ''}.`;
    });
  } else $('catCerca').hidden = true;
  if (idx.livelli_analitici.accessibilita.presente) { mostraAccessibilita(0); $('s_acc').addEventListener('change', (e) => mostraAccessibilita(+e.target.value)); }
  if (idx.livelli_analitici.scenari.presente) {
    const accendi = () => { $('l_scenari').checked = true; $('l_scenari').dispatchEvent(new Event('change')); };
    mostraScenario(0);
    const vaiScn = () => { accendi(); vai(scnCentro.clone().add(new THREE.Vector3(0.3 * scnL, 2 * scnL, 0.9 * scnL)), scnCentro); };   // quasi dall'alto: gli edifici non coprono l'intervento
    $('scnLista').addEventListener('change', (e) => { mostraScenario(+e.target.value); vaiScn(); });
    $('vScn').addEventListener('click', vaiScn);
    // il sole dell'istante dei numeri (15 luglio, metà della punta 12:30-13:30): ombra vista e numeri parlano dello stesso momento
    $('scnSole').addEventListener('click', () => { $('data').value = '2026-07-15'; $('ora').value = 780; aggiornaSole(); accendi(); });
  } else for (const id of ['vScn', 'scnSole']) $(id).disabled = true;
  if (idx.livelli_analitici.ombra.presente) {
    mostraOmbra(0); $('s_om').addEventListener('change', (e) => mostraOmbra(+e.target.value));
    const bb = new THREE.Box3(); for (const q of dati.ombra.percorsi || []) for (let k = 0; k < q.p.length; k += 2) bb.expandByPoint(new THREE.Vector3(q.p[k], 0, q.p[k + 1]));
    const c = bb.getCenter(new THREE.Vector3()), L = Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z, 200); c.y = tY(c.x, c.z);
    $('vOm').addEventListener('click', () => { $('l_ombra').checked = true; $('l_ombra').dispatchEvent(new Event('change')); vai(c.clone().add(new THREE.Vector3(0.3 * L, 0.9 * L, 0.6 * L)), c); });
  }

  // --- sole ---------------------------------------------------------------------
  const fondo = new THREE.Color(), giorno = new THREE.Color(0xeef0ec), notte = new THREE.Color(0x1a2036);
  scene.fog = new THREE.Fog(0xeef0ec, 1600, 5200);
  function aggiornaSole() {
    const [y, mo, d] = $('data').value.split('-').map(Number), min = +$('ora').value, h = Math.floor(min / 60), mi = min % 60;
    $('oraTesto').textContent = `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
    $('ora').setAttribute('aria-valuetext', $('oraTesto').textContent);
    const { alt, az } = sunPos(romeToUtc(y, mo, d, h, mi), LAT, LON);
    const ad = alt / RAD, azd = az / RAD, su = alt > 0.02;
    $('sole').textContent = su ? `Sole: altezza ${ad.toFixed(0)} gradi, direzione ${PUNTI[Math.round(azd / 45) % 8]} (${azd.toFixed(0)} gradi)` : 'Il sole è sotto l\'orizzonte: nessuna ombra.';
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(alt), Math.sin(Math.max(alt, 0.02)), -Math.cos(az) * Math.cos(alt)).normalize();
    sun.position.copy(dir).multiplyScalar(2500); sun.target.position.set(0, 0, 0); sun.target.updateMatrixWorld();
    const f = Math.min(Math.max(alt / 0.25, 0), 1);
    sun.intensity = su ? 2.8 * f + 0.3 : 0; sun.castShadow = su; hemi.intensity = 0.2 + 0.45 * f;
    sun.color.set(0xff9a4d).lerp(new THREE.Color(0xfff4de), Math.min(Math.max(alt / 0.5, 0), 1));
    fondo.copy(notte).lerp(giorno, f); scene.background = fondo; scene.fog.color.copy(fondo);
    shadowDirty = dirty = true;
  }
  $('data').addEventListener('input', aggiornaSole); $('ora').addEventListener('input', aggiornaSole);
  aggiornaSole();

  // --- schede ---------------------------------------------------------------------
  const CLA = { derived: 'misurata dal rilievo laser 2023', estimated: 'stimata' };
  const ORIGINE = { 'lidar_2023+uv_rt_2011': 'rilievo laser (LiDAR) 2023, confrontato con i volumi regionali del 2011', uv_rt_2011: 'volumi regionali del 2011 (il rilievo laser non basta: edificio piccolo o poche misure)', 'osm+lidar_2023': 'impronta da OpenStreetMap, altezza dal rilievo laser 2023' };
  const TIPO = { volume_uv: 'volume del database topografico regionale', volume_nuovo: 'edificio nuovo dopo il 2011 (OpenStreetMap e rilievo laser)', copertura_osm: 'tettoia o copertura (OpenStreetMap)' };
  const CAMBIO = { '': 'nessuno rilevato', non_confrontato: 'non confrontabile (edificio sotto 40 m²)', lidar_piu_alto: 'più alto nel 2023: probabile sopraelevazione o ampliamento', lidar_piu_basso: 'più basso nel 2023', demolizione_probabile: 'probabile demolizione: nel 2023 il rilievo laser non lo trova', lidar_sotto_1m: 'volume basso, non distinguibile dal terreno nel rilievo laser', sotto_2_5m: 'sotto 2,5 m: probabile tettoia o baracca', vegetazione_possibile: 'possibile vegetazione sul tetto', scarto_con_vegetazione: 'alberi vicini: confronto incerto' };
  const MOTIVO = { poche_celle_chioma: 'poche misure della chioma nel rilievo laser', sotto_2_5m: 'chioma sotto 2,5 m nel rilievo laser', in_edificio: 'posizione dentro un edificio', coperto_da_edificio: 'chioma coperta da un edificio' };
  const m1 = (v) => (v == null ? null : Number(v).toFixed(1));
  const riga = (k, v) => (v == null || v === '' ? '' : `<dt>${k}</dt><dd>${/^https?:/.test(v) ? `<a href="${v}" target="_blank" rel="noopener">${v}</a>` : v}</dd>`);
  const iv = (a, b) => (a != null && b != null ? ` (da ${a} a ${b})` : '');
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const lista = (righe) => righe.map(([k, v]) => riga(k, v == null ? v : esc(String(v).replace(/(\d)\.(\d)/g, '$1,$2')))).join(''); // decimali con la virgola
  function scheda(titolo, righe, livello, extra, tecnici) {
    $('schedaTit').textContent = titolo;
    $('schedaDati').innerHTML = lista(righe);
    const fonti = idx.livelli[livello].fonti.map((id) => idx.fonti.find((f) => f.id === id));
    $('schedaFonte').innerHTML = `<details><summary>Fonti dei dati (${fonti.length})</summary>` + fonti.map((f) => `${esc(f.titolo)}, ${esc(f.ente)}. Licenza ${esc(f.licenza)}${f.riserva ? ' (con riserva)' : ''}. Scaricato il ${f.scaricato}. <a href="${f.url}" target="_blank" rel="noopener">scheda del dato</a>`).join('<br>') + '</details>';
    if (extra) $('schedaFonte').innerHTML = extra;
    const t = (tecnici || []).filter(([, v]) => v != null && v !== '');
    if (t.length) $('schedaFonte').innerHTML += `<details><summary>Dettagli tecnici</summary><dl>${t.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl></details>`;
    $('scheda').hidden = false;
  }
  const chiudi = () => { $('scheda').hidden = true; evid.visible = false; dirty = true; };
  $('chiudi').addEventListener('click', chiudi);
  addEventListener('keydown', (e) => { if (e.key === 'Escape') chiudi(); });

  const evid = new THREE.Mesh(new THREE.RingGeometry(1, 1.25, 32).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xff6600, side: THREE.DoubleSide, depthTest: false })); evid.renderOrder = 20; evid.visible = false; scene.add(evid);
  let evEd = null;
  const anello = (x, y, z, r) => { evid.position.set(x, y + 0.5, z); evid.scale.setScalar(r); evid.visible = true; };

  const ray = new THREE.Raycaster();
  let down = null;
  canvas.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY]; });
  canvas.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; down = null;
    const r = canvas.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
    const lista = [edMesh, chiome, ...sel, ...scnPick, tMesh].filter(Boolean).filter((o) => o.parent && o.visible && (!o.parent.isGroup || o.parent.visible));
    const hit = ray.intersectObjects(lista, false)[0];
    if (evEd) { scene.remove(evEd); evEd.geometry.dispose(); evEd = null; }
    if (!hit) { chiudi(); return; }
    const o = hit.object;
    if (o === edMesh) {
      const v = hit.faceIndex * 3; let lo = 0, hi = edStart.length - 2;
      while (lo < hi) { const m = (lo + hi + 1) >> 1; if (edStart[m] <= v) lo = m; else hi = m - 1; }
      const b = dati.edifici.edifici[lo];
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(edMesh.geometry.attributes.position.array.slice(edStart[lo] * 3, edStart[lo + 1] * 3), 3)); g.computeVertexNormals();
      evEd = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0xff7a1a, emissive: 0x552200 })); scene.add(evEd);
      scheda(b.nome || (b.ind ? 'Edificio in ' + b.ind : 'Edificio'), [
        ['Civico più vicino', b.ind ? b.ind + ' (entro 15 m, non verificato)' : 'nessuno entro 15 m'],
        ['Altezza', `${m1(b.h)} m${b.h_min != null ? ` (fra ${m1(b.h_min)} e ${m1(b.h_max)} m)` : ''}`],
        ['Come è misurata', ORIGINE[b.fonte] || b.fonte],
        ['Rilievo laser 2023', b.h_lidar != null ? m1(b.h_lidar) + ' m' : null], ['Volumi regionali 2011', b.h_uv != null ? m1(b.h_uv) + ' m' : null],
        ['Cambiamenti dal 2011', CAMBIO[b.flag] ?? b.flag], ['Tipo', TIPO[b.tipo] || b.tipo],
        ['Superficie', Math.round(b.area_m2).toLocaleString('it-IT') + ' m²'], ['Quota del terreno', m1(b.z_base) + ' m sul livello del mare'],
        ['Catasto', b.cat?.length ? b.cat.join(', ') + ' (aggancio geometrico, non verificato)' : (b.cat ? 'nessuna particella contiene l\'edificio' : null)],
        ['Portici o volumi sospesi', 'non noti (nessuna fonte)']], 'edifici', null,
        [['Codice', b.id], ['Classe dell\'altezza', b.classe_h], ['Origine', b.fonte], ['Segnalazione', b.flag], ['Tipo', b.tipo], ['Presente nel 2023', String(b.presente_2023)]]);
    } else if (o === tMesh) {
      const i = Math.min(TM.ny - 1, Math.floor((1 - hit.uv.y) * TM.ny)) * TM.nx + Math.min(TM.nx - 1, Math.floor(hit.uv.x * TM.nx));
      const d = TM.date[+tVista], q = tVista === 'sopra_40' ? TM.sopra_40[i] : (d ? d.t : TM.media)[i];
      anello(hit.point.x, hit.point.y, hit.point.z, TM.passo / 2);
      scheda('Temperatura della superficie', [
        [tVista === 'sopra_40' ? 'Giornate sopra 40 °C' : 'Temperatura', tVista === 'sopra_40' ? `${q} su ${TM.validi_per_cella[i]} valide` : q === TM.nodata ? 'non valida in questa cella (nubi o acqua)' : (q / 10).toFixed(1) + ' °C'],
        ['Giornata', d ? `${d.data}, ore ${d.ora_utc} UTC, ${d.satellite}` : `media di ${TM.validi_per_cella[i]} giornate estive serene`],
        ['Cella', `${TM.passo} x ${TM.passo} m (misura termica a 100 m)`],
        ['Cosa misura', 'la temperatura della superficie (tetti, asfalto, prato), non dell\'aria']], 'temperature');
    } else if (o === chiome) {
      const a = dati.alberi.alberi[hit.instanceId]; anello(a.x, a.y, a.z, Math.max((a.d ?? 3) / 2, 1.5));
      scheda(a.specie ? a.specie.charAt(0).toUpperCase() + a.specie.slice(1).toLowerCase() : 'Albero', [['Altezza', `${a.h} m${iv(a.h_min, a.h_max)}, ${CLA[a.h_cls]}`], ['Diametro della chioma', `${a.d} m${iv(a.d_min, a.d_max)}, ${CLA[a.ch_cls]}`], ['Circonferenza del tronco', a.circ != null ? a.circ + ' cm' : null], ['Perché è stimata', a.motivo ? MOTIVO[a.motivo] || a.motivo : null], ['Quota del terreno', (a.y + idx.area.quota_riferimento_m).toFixed(1) + ' m sul livello del mare']], 'alberi', null,
        [['Codice', a.id], ['Classe dell\'altezza', a.h_cls], ['Classe della chioma', a.ch_cls], ['Motivo', a.motivo]]);
    } else if (o.userData.scn) {
      const S = o.userData.scn, it = o.userData.pens || S.alberi[hit.instanceId];
      if (o.userData.pens) anello(hit.point.x, hit.point.y - 1, hit.point.z, 6); else anello(it.x, tY(it.x, it.z), it.z, Math.max(it.d / 2, 1.5));
      const dim = o.userData.pens ? [['Quota intradosso', `${it.z_lo} m sul suolo`], ['Quota tetto', `${it.z_hi} m sul suolo`]] : [['Altezza', it.h + ' m'], ['Diametro della chioma', it.d + ' m'], ['Imposta della chioma', it.imp + ' m']];
      scheda((o.userData.pens ? 'Pensilina ipotetica ' : 'Albero ipotetico ') + it.id.split(':').pop(), [['Scenario', S.etichetta], ...dim, ...S.numeri, ['Fattibilità', S.fattibilita]], 'scenari',
        `<strong>Fonte dei numeri</strong><br>${esc(dati.interventi.fonte_numeri)}. Interventi: scenarios/firenze_novoli/interventi.geojson.`);
    } else {
      const p = o.userData.punto; anello(p.x, tY(p.x, p.z), p.z, 10);
      scheda(p.nome, Object.entries(p.attr || {}), o.userData.tipo);
    }
    dirty = true;
  });

  // --- fonti e limiti ------------------------------------------------------------
  $('fonti').innerHTML = idx.fonti.map((f) => `<li><strong>${esc(f.titolo)}</strong><br>${esc(f.ente)}. Licenza ${esc(f.licenza)}${f.riserva ? ' (con riserva: ' + esc(f.riserva) + ')' : ''}. Scaricato il ${f.scaricato}. ${f.periodo ? esc(f.periodo) + '. ' : ''}Uso: ${esc(f.uso)}. <a href="${f.url}" target="_blank" rel="noopener">scheda del dato</a></li>`).join('');
  $('limiti').innerHTML = idx.limiti.map((l) => `<li>${esc(l)}</li>`).join('');

  // --- viste e ciclo -------------------------------------------------------------
  $('vReset').onclick = () => vai(VISTA.pos, VISTA.tgt);
  // 2D: vista dall'alto sul punto guardato; 3D: torna obliqua alla stessa distanza
  const dall_alto = () => controls.getPolarAngle() < 0.05;
  $('vAlto').onclick = () => {
    const t = controls.target.clone(), d = camera.position.distanceTo(t);
    if (dall_alto()) vai(t.clone().add(VISTA.pos.clone().sub(VISTA.tgt).normalize().multiplyScalar(d)), t);
    else vai(t.clone().add(new THREE.Vector3(0, d, 0.01)), t);
  };
  // bussola: il segno indica il nord sullo schermo; il clic riporta il nord in alto
  $('vNord').onclick = () => {
    const t = controls.target, o = camera.position.clone().sub(t), r = Math.hypot(o.x, o.z);
    vai(t.clone().add(new THREE.Vector3(0, o.y, Math.max(r, 0.01))), t.clone());
  };
  const aggiornaComandi = () => {
    $('bussola').style.transform = `rotate(${controls.getAzimuthalAngle()}rad)`;
    const a = dall_alto(); $('vAlto').textContent = a ? '3D' : '2D';
    $('vAlto').setAttribute('aria-label', a ? 'Vista obliqua in 3D' : 'Vista dall\'alto in 2D'); $('vAlto').title = $('vAlto').getAttribute('aria-label');
  };
  if (!document.fullscreenEnabled) $('vSchermo').hidden = true;
  $('vSchermo').onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());
  $('vPiu').onclick = () => { camera.position.lerp(controls.target, 0.25); dirty = true; };
  $('vMeno').onclick = () => { camera.position.lerp(controls.target, -0.3); dirty = true; };
  controls.addEventListener('change', () => { dirty = true; });
  const nr = () => { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); dirty = true; };
  addEventListener('resize', nr); nr();
  // pannello: si chiude e si riapre dal pulsante in alto; sul telefono parte chiuso
  const pannello = (aperto) => { $('pCorpo').hidden = !aperto; $('pApri').setAttribute('aria-expanded', aperto); $('pApri').setAttribute('aria-label', aperto ? 'Chiudi il pannello' : 'Apri il pannello'); $('pApri').textContent = aperto ? '−' : '+'; };
  $('pApri').onclick = () => pannello($('pCorpo').hidden);
  if (matchMedia('(max-width:700px)').matches) pannello(false);
  vai(VISTA.pos, VISTA.tgt);
  (function ciclo() {
    controls.update();
    if (dirty) { if (shadowDirty) { renderer.shadowMap.needsUpdate = true; shadowDirty = false; } renderer.render(scene, camera); posaEtichette(); aggiornaComandi(); dirty = false; }
    requestAnimationFrame(ciclo);
  })();
  const nE = dati.edifici.n.toLocaleString('it-IT'), nA = dati.alberi.n.toLocaleString('it-IT');
  stato(`Pronto: ${nE} edifici, ${nA} alberi, ${dati.rete.n.toLocaleString('it-IT')} tratti di rete. Dati: ${(Object.values(idx.assets).reduce((s, a) => s + a.byte, 0) / 1e6).toFixed(1)} MB compressi.`);
  window.scena = { THREE, scene, camera, sunPos, romeToUtc, pronta: true };
}
main().catch((e) => { console.error(e); stato('Errore nel caricamento: ' + e.message); });
