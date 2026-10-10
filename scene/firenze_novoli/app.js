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

  const hemi = new THREE.HemisphereLight(0xdfeaf5, 0x8a8f78, 0.9); scene.add(hemi);
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
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setIndex(ix); g.computeVertexNormals();
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0xc9d1b8, roughness: 1 })); m.receiveShadow = true;
    gruppi.terreno = m; scene.add(m);
  }

  // edifici
  const COL = { measured: 0xbfc3c9, derived: 0xdccbA8, assente: 0x666b73 };
  let edMesh, edStart = [];
  {
    const E = dati.edifici, pos = f32(E.posizioni), col = new Float32Array(pos.length), c = new THREE.Color();
    let v = 0;
    for (const e of E.edifici) {
      edStart.push(v); c.set(e.presente_2023 ? COL[e.classe_h] : COL.assente);
      for (let i = v; i < v + e.n; i++) col.set([c.r, c.g, c.b], i * 3);
      v += e.n;
    }
    edStart.push(v);
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeVertexNormals();
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
      c.set(a.ch_cls === 'estimated' ? 0x86b564 : 0x3d7a37); chiome.setColorAt(i, c);
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

  // punti: destinazioni, tram, scuole, rifugi, barriere
  const PUNTO = { destinazioni: [0xd9480f, 5, 14], tram: [0x00a8e8, 6, 26], scuole: [0x7048e8, 6, 26], rifugi: [0x2f9e44, 6, 22], barriere: [0xc2255c, 1.6, 5] };
  // icone: cerchio col colore del livello e una lettera (T tram, S scuola, R rifugio climatico)
  const ICONE = {};
  for (const [k, l] of [['tram', 'T'], ['scuole', 'S'], ['rifugi', 'R']]) {
    const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
    x.beginPath(); x.arc(32, 32, 29, 0, 7); x.fillStyle = '#' + PUNTO[k][0].toString(16).padStart(6, '0'); x.fill(); x.lineWidth = 4; x.strokeStyle = '#fff'; x.stroke();
    x.fillStyle = '#fff'; x.font = 'bold 40px system-ui, sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(l, 32, 35);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; ICONE[k] = { url: c.toDataURL(), t };
  }
  const sfera = new THREE.SphereGeometry(1, 12, 8), palo = new THREE.CylinderGeometry(0.25, 0.25, 1, 6);
  for (const k of Object.keys(PUNTO)) { gruppi[k] = new THREE.Group(); scene.add(gruppi[k]); }
  for (const p of dati.punti.punti) {
    const [col, r, h] = PUNTO[p.livello], g = gruppi[p.livello], q = new THREE.Group();
    const ic = ICONE[p.livello], m = ic ? new THREE.Sprite(new THREE.SpriteMaterial({ map: ic.t })) : new THREE.Mesh(sfera, new THREE.MeshStandardMaterial({ color: col, roughness: 0.6 }));
    m.scale.setScalar(ic ? 3 * r : r); m.position.y = h; m.userData = { tipo: p.livello, punto: p }; q.add(m); sel.push(m);
    const s = new THREE.Mesh(palo, m.isSprite ? new THREE.MeshStandardMaterial({ color: col }) : m.material); s.scale.y = h; s.position.y = h / 2; q.add(s);
    q.position.set(p.x, tY(p.x, p.z), p.z); g.add(q);
    if (p.contorno) g.add(nastri([{ p: p.contorno }], 0.4, () => 2, () => hex(col)));
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
    $('leg_ombra').innerHTML = pc + `<span>istante del calcolo: ${I.istante} (non segue il cursore dell'ora)</span>`;
  }

  // scenari: interventi ipotetici (livello spento all'avvio)
  const COL_SCN = 0xe0218a;
  let scnGruppo = null, scnCentro = null, scnPick = [];
  function mostraScenario(i) {
    if (scnGruppo) { scene.remove(scnGruppo); scnGruppo.traverse((o) => o.geometry?.dispose()); }
    const S = dati.interventi.scenari[i], g = new THREE.Group(), m = new THREE.Matrix4(), q = new THREE.Quaternion();
    scnPick = []; let sx = 0, sz = 0, n = 0;
    if (S.alberi.length) {
      const cr = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: COL_SCN, roughness: 1, flatShading: true }), S.alberi.length);
      const tr = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 1, 8), new THREE.MeshStandardMaterial({ color: 0x7a1450, roughness: 1 }), S.alberi.length);
      S.alberi.forEach((a, k) => {
        const y = tY(a.x, a.z), hc = a.h - a.imp;
        m.compose(new THREE.Vector3(a.x, y + a.imp + hc / 2, a.z), q, new THREE.Vector3(a.d / 2, hc / 2, a.d / 2)); cr.setMatrixAt(k, m);
        m.compose(new THREE.Vector3(a.x, y + a.imp / 2, a.z), q, new THREE.Vector3(0.2, a.imp, 0.2)); tr.setMatrixAt(k, m);
        sx += a.x; sz += a.z; n++;
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
      sx += cx; sz += cz; n++;
    }
    scnCentro = new THREE.Vector3(sx / n, 0, sz / n); scnCentro.y = tY(scnCentro.x, scnCentro.z);
    g.visible = $('l_scenari').checked; scnGruppo = g; gruppi.scenari = g; scene.add(g); shadowDirty = dirty = true;
  }

  // --- pannello livelli ---------------------------------------------------------
  const box = $('livelli');
  for (const [k, L] of Object.entries(idx.livelli)) {
    const an = ['accessibilita', 'ombra', 'scenari'].includes(k), presente = !an || idx.livelli_analitici[k].presente;
    const w = document.createElement('div');
    w.innerHTML = `<label><input type="checkbox" id="l_${k}" ${presente ? '' : 'disabled'} ${!an && k !== 'barriere' ? 'checked' : ''}> ${L.etichetta}${presente ? '' : ' <em>(dati non presenti)</em>'}</label>`;
    if (PUNTO[k]) w.innerHTML += `<div class="leg"><span>${ICONE[k] ? `<img src="${ICONE[k].url}" alt="" width="16" height="16" style="vertical-align:-3px;margin-right:4px">` : `<i style="background:#${PUNTO[k][0].toString(16).padStart(6, '0')};border-radius:50%"></i>`}segnaposto</span></div>`;
    if (k === 'edifici') w.innerHTML += '<div class="leg"><span><i style="background:#bfc3c9"></i>altezza misurata</span><span><i style="background:#dccba8"></i>altezza derivata</span><span><i style="background:#666b73"></i>non presente nel 2023</span></div>';
    if (k === 'destinazioni') w.innerHTML += '<div class="leg"><span>I punti di arrivo dei calcoli di accessibilità e ombra: i 7 ingressi del Polo delle Scienze Sociali, le scuole Vamba (primaria e infanzia), le fermate T2 San Donato - Università, Regione Toscana e Torre degli Agli.</span></div>';
    if (k === 'alberi') w.innerHTML += '<div class="leg"><span><i style="background:#3d7a37"></i>chioma misurata</span><span><i style="background:#86b564"></i>chioma stimata</span></div>';
    if (k === 'rete') w.innerHTML += '<div class="leg"><span><i style="background:#5b6470"></i>strada</span><span><i style="background:#b0763a"></i>sentiero</span><span><i style="background:#2f6fb5"></i>marciapiede</span><span><i style="background:#f2f2f2"></i>attraversamento</span></div>';
    if (k === 'accessibilita' && presente) w.innerHTML += `<div class="sub"><label for="s_acc">Verso:</label><select id="s_acc">${dati.accessibilita.destinazioni.map((d, i) => `<option value="${i}">${d.nome}</option>`).join('')}</select></div><div class="leg" id="leg_accessibilita"></div>`;
    if (k === 'ombra' && presente) w.innerHTML += `<div class="sub"><label for="s_om">Istante:</label><select id="s_om">${dati.ombra.istanti.map((d, i) => `<option value="${i}">${d.istante}</option>`).join('')}</select></div><div class="riga" style="margin-top:6px"><button type="button" id="vOm">Vai ai percorsi</button></div><div class="leg"><span>Due percorsi campione verso il Polo universitario.</span><span><i style="background:#f2c230"></i>al sole</span><span><i style="background:#1b2a6b"></i>in ombra</span></div><div class="leg" id="leg_ombra"></div>`;
    if (k === 'scenari' && presente) w.innerHTML += `<div class="sub"><label for="s_scn">Scenario:</label><select id="s_scn">${dati.interventi.scenari.map((d, i) => `<option value="${i}">${d.etichetta}</option>`).join('')}</select><div class="riga" style="margin-top:6px"><button type="button" id="vScn">Vai all'intervento</button></div></div><div class="leg"><span><i style="background:#e0218a"></i>albero o pensilina ipotetici</span></div>`;
    box.appendChild(w);
  }
  for (const k of Object.keys(idx.livelli)) {
    const cb = $('l_' + k);
    if (gruppi[k]) gruppi[k].visible = cb.checked;
    cb.addEventListener('change', () => { if (gruppi[k]) gruppi[k].visible = cb.checked; shadowDirty = dirty = true; });
  }
  if (idx.livelli_analitici.accessibilita.presente) { mostraAccessibilita(0); $('s_acc').addEventListener('change', (e) => mostraAccessibilita(+e.target.value)); }
  if (idx.livelli_analitici.scenari.presente) {
    mostraScenario(0); $('s_scn').addEventListener('change', (e) => mostraScenario(+e.target.value));
    $('vScn').addEventListener('click', () => { $('l_scenari').checked = true; $('l_scenari').dispatchEvent(new Event('change')); vai(scnCentro.clone().add(new THREE.Vector3(25, 95, 55)), scnCentro); });
  }
  if (idx.livelli_analitici.ombra.presente) {
    mostraOmbra(0); $('s_om').addEventListener('change', (e) => mostraOmbra(+e.target.value));
    const bb = new THREE.Box3(); for (const q of dati.ombra.percorsi || []) for (let k = 0; k < q.p.length; k += 2) bb.expandByPoint(new THREE.Vector3(q.p[k], 0, q.p[k + 1]));
    const c = bb.getCenter(new THREE.Vector3()), L = Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z, 200); c.y = tY(c.x, c.z);
    $('vOm').addEventListener('click', () => { $('l_ombra').checked = true; $('l_ombra').dispatchEvent(new Event('change')); vai(c.clone().add(new THREE.Vector3(0.3 * L, 0.9 * L, 0.6 * L)), c); });
  }

  // --- sole ---------------------------------------------------------------------
  const fondo = new THREE.Color(), giorno = new THREE.Color(0xcfe3f2), notte = new THREE.Color(0x1a2036);
  scene.fog = new THREE.Fog(0xcfe3f2, 2500, 7000);
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
  const CL = { measured: 'misurata', derived: 'derivata', estimated: 'stimata' };
  const CLA = { derived: 'misurata dal LiDAR', estimated: 'stimata' };
  const riga = (k, v) => (v == null || v === '' ? '' : `<dt>${k}</dt><dd>${/^https?:/.test(v) ? `<a href="${v}" target="_blank" rel="noopener">${v}</a>` : v}</dd>`);
  const iv = (a, b) => (a != null && b != null ? ` (da ${a} a ${b})` : '');
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function scheda(titolo, righe, livello, extra) {
    $('schedaTit').textContent = titolo;
    $('schedaDati').innerHTML = righe.map(([k, v]) => riga(k, v == null ? v : esc(String(v).replace(/(\d)\.(\d)/g, '$1,$2')))).join(''); // decimali con la virgola
    const fonti = idx.livelli[livello].fonti.map((id) => idx.fonti.find((f) => f.id === id));
    $('schedaFonte').innerHTML = '<strong>Fonte</strong><br>' + fonti.map((f) => `${esc(f.titolo)}, ${esc(f.ente)}. Licenza ${esc(f.licenza)}${f.riserva ? ' (con riserva)' : ''}. Scaricato il ${f.scaricato}. <a href="${f.url}" target="_blank" rel="noopener">scheda del dato</a>`).join('<br>');
    if (extra) $('schedaFonte').innerHTML = extra;
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
    const lista = [edMesh, chiome, ...sel, ...scnPick].filter((o) => o.parent && o.visible && (!o.parent.isGroup || o.parent.visible));
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
      scheda('Edificio ' + b.id.replace('bld_', ''), [['Altezza', `${b.h} m${iv(b.h_min, b.h_max)}`], ['Classe dell\'altezza', CL[b.classe_h]], ['Altezza LiDAR 2023', b.h_lidar != null ? b.h_lidar + ' m' : null], ['Altezza del 2011', b.h_uv != null ? b.h_uv + ' m' : null], ['Quota di base', b.z_base + ' m s.l.m.'], ['Area', b.area_m2 + ' m²'], ['Tipo', b.tipo], ['Presente nel 2023', b.presente_2023 ? 'sì' : 'no, probabile demolizione'], ['Segnalazione', b.flag], ['Portico o volume sospeso', 'ignoto (nessuna fonte)'], ['Origine dell\'altezza', b.fonte]], 'edifici');
    } else if (o === chiome) {
      const a = dati.alberi.alberi[hit.instanceId]; anello(a.x, a.y, a.z, Math.max((a.d ?? 3) / 2, 1.5));
      scheda(a.specie || 'Albero', [['Altezza', `${a.h} m${iv(a.h_min, a.h_max)}, ${CLA[a.h_cls]}`], ['Diametro della chioma', `${a.d} m${iv(a.d_min, a.d_max)}, ${CLA[a.ch_cls]}`], ['Circonferenza del tronco', a.circ != null ? a.circ + ' cm' : null], ['Motivo della stima', a.motivo ? a.motivo.replaceAll('_', ' ') : null], ['Quota di base', (a.y + idx.area.quota_riferimento_m).toFixed(1) + ' m s.l.m.'], ['Codice', a.id]], 'alberi');
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
  $('vAlto').onclick = () => vai(new THREE.Vector3(0, 1700, 1), VISTA.tgt);
  $('vPiu').onclick = () => { camera.position.lerp(controls.target, 0.25); dirty = true; };
  $('vMeno').onclick = () => { camera.position.lerp(controls.target, -0.3); dirty = true; };
  controls.addEventListener('change', () => { dirty = true; });
  const nr = () => { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); dirty = true; };
  addEventListener('resize', nr); nr();
  if (matchMedia('(max-width:700px)').matches) $('pannello').open = false;
  vai(VISTA.pos, VISTA.tgt);
  (function ciclo() {
    controls.update();
    if (dirty) { if (shadowDirty) { renderer.shadowMap.needsUpdate = true; shadowDirty = false; } renderer.render(scene, camera); dirty = false; }
    requestAnimationFrame(ciclo);
  })();
  const nE = dati.edifici.n.toLocaleString('it-IT'), nA = dati.alberi.n.toLocaleString('it-IT');
  stato(`Pronto: ${nE} edifici, ${nA} alberi, ${dati.rete.n.toLocaleString('it-IT')} tratti di rete. Dati: ${(Object.values(idx.assets).reduce((s, a) => s + a.byte, 0) / 1e6).toFixed(1)} MB compressi.`);
  window.scena = { THREE, scene, camera, sunPos, romeToUtc, pronta: true };
}
main().catch((e) => { console.error(e); stato('Errore nel caricamento: ' + e.message); });
