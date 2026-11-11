#!/usr/bin/env python3
"""Genera el proyecto KiCad de la placa v2 (rf_cc1101_v2.kicad_pro / _pcb / _sch).

Placa minima: zocalos para ESP32-C3 SuperMini (2 x 1x8, en horizontal con el USB
saliendo por el lateral derecho; misma asignacion de pines que la v1 que ya funciona)
+ zocalo 2x4 del E07-M1101D (CC1101), con el modulo y la antena asomando por el
borde de arriba, + condensador electrolitico de
100 uF entre 3V3 y GND (arriba a la derecha, al lado del zocalo del CC1101).
Sin XIAO, sin GDO2 (se usa pin unico GDO0) y sin cabecera I2C.
Variante C: todo en linea (USB por la izquierda, CC1101 saliendo por la derecha) para caja baja.
Variante D: SuperMini (USB por la izquierda) | condensador | CC1101 al lado, con la antena hacia arriba.
Variante X: como la D pero con zocalos para XIAO ESP32-C6 (USB por la izquierda).
Python puro (sin numpy). Uso: python3 generador_placa_v2.py <carpeta_salida> [A|B|C|D|X]
"""
import heapq, math, os, sys, uuid

# ------------------------------------------------------------------ parametros
SM_ROW = 15.24       # distancia entre filas de pines del C3 SuperMini (comprobada en la v1)
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
NAME = "rf_cc1101_v2"

G = 0.254            # rejilla del router (mm)
TW, CLR = 0.3, 0.2   # ancho de pista, holgura
VIA_D, VIA_DR = 0.8, 0.4
PAD_D, DRILL = 1.7, 1.0
BX0, BY0, BX1, BY1 = 0.0, 0.0, 20.828, 25.4   # contorno (coord. locales)
OX, OY = 100.0, 60.0  # desplazamiento para colocar la placa en la hoja
EDGE = 0.6           # margen pistas-borde

NETS = ["GND", "3V3", "SCK", "MISO", "MOSI", "CS", "GDO0"]
NID = {n: i + 1 for i, n in enumerate(NETS)}
U = lambda: str(uuid.uuid4())
ROOT = U()

# ------------------------------------------------------------------ componentes
def socket1(ref, value, x, y, pins, fpid, side):
    # fila horizontal: pin 1 a la izquierda, el ultimo junto al USB (derecha)
    pads = [dict(num=str(i + 1), name=name, net=net, x=x + i * 2.54, y=y, kind="thru",
                 rect=(i == 0), w=PAD_D, h=PAD_D, drill=DRILL, side=side)
            for i, (name, net) in enumerate(pins)]
    return dict(ref=ref, value=value, fpid=fpid, x=x, y=y, pads=pads, sym=U())

def socket2x4_rot(ref, value, x, y, pins, fpid):
    # zocalo girado: los 4 pares van en horizontal y el modulo sale hacia arriba (-y).
    # pines impares (1,3,5,7) en la fila de abajo, pares (2,4,6,8) en la de arriba.
    pads = []
    for n, (name, net) in enumerate(pins):
        c, r = n % 2, n // 2
        pads.append(dict(num=str(n + 1), name=name, net=net, x=x + r * 2.54, y=y - c * 2.54, kind="thru",
                         rect=(n == 0), w=PAD_D, h=PAD_D, drill=DRILL, side="D" if c == 0 else "A"))
    return dict(ref=ref, value=value, fpid=fpid, x=x, y=y, pads=pads, sym=U())

def socket2x4(ref, value, x, y, pins, fpid):
    # zocalo sin girar (como en la v1): el modulo sale hacia la derecha (+x)
    pads = []
    for n, (name, net) in enumerate(pins):
        c, r = n % 2, n // 2
        pads.append(dict(num=str(n + 1), name=name, net=net, x=x + c * 2.54, y=y + r * 2.54, kind="thru",
                         rect=(n == 0), w=PAD_D, h=PAD_D, drill=DRILL, side="L" if c == 0 else "R"))
    return dict(ref=ref, value=value, fpid=fpid, x=x, y=y, pads=pads, sym=U())

def cp_radial(ref, value, x, y, net_pos, net_neg, vertical=False):
    # CP_Radial_D5.0mm_P2.00mm: + a la izquierda y - a la derecha (o + arriba y - abajo si vertical)
    dx, dy = (0, 2.0) if vertical else (2.0, 0)
    pads = [dict(num="1", name="+", net=net_pos, x=x, y=y, kind="thru", rect=True, w=1.6, h=1.6, drill=0.8, side="R"),
            dict(num="2", name="-", net=net_neg, x=x + dx, y=y + dy, kind="thru", rect=False, w=1.6, h=1.6, drill=0.8, side="R")]
    return dict(ref=ref, value=value, fpid="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm", x=x, y=y, pads=pads,
                sym=U(), circle=(dx / 2, dy / 2, 2.5), plus=(-1.4, 0.3) if vertical else (0, -1.4))

S7 = "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical"
S8 = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"
S24 = "Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical"

# ESP32-C3 SuperMini con el USB a la derecha (la v1 tenia el USB abajo; mismo modulo girado 90 grados)
sm_L = [("5V", None), ("GND", "GND"), ("3V3", "3V3"), ("G4", "SCK"), ("G3", "GDO0"),
        ("G2", None), ("G1", None), ("G0", None)]
sm_R = [("G5", "MISO"), ("G6", "MOSI"), ("G7", "CS"), ("G8", None), ("G9", None),
        ("G10", None), ("G20", None), ("G21", None)]

# XIAO ESP32-C6 con el USB arriba (igual que en la v1): columna izquierda y derecha, de arriba abajo.
# Sin GDO2 ni I2C. GPIO3 del C6 no sale a los pines (conmutador de antena).
xiao_L = [("D0", None), ("D1", "CS"), ("D2", "GDO0"), ("D3", None), ("D4", None), ("D5", None), ("D6", None)]
xiao_R = [("5V", None), ("GND", "GND"), ("3V3", "3V3"), ("D10", "MOSI"), ("D9", "MISO"), ("D8", "SCK"), ("D7", None)]

# E07-M1101D (disposicion NRF24L01: GND VCC GDO0 CSN SCK MOSI MISO GDO2); GDO2 sin usar
cc_pins = [("GND", "GND"), ("VCC", "3V3"), ("GDO0", "GDO0"), ("CSN", "CS"),
           ("SCK", "SCK"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("GDO2", None)]

XS = 1.524           # primer pin (lado contrario al USB) de las dos filas del SuperMini
# Variante A: modulo de 15 mm centrado (el condensador queda medio debajo del modulo).
# Variante B: modulo pegado al borde izquierdo; el condensador queda libre a la derecha.
VARIANT = sys.argv[2].upper() if len(sys.argv) > 2 else "A"
X_CC = 3.81 if VARIANT == "B" else 6.604   # pin 1 del CC1101
Y_CC = 4.318          # fila de abajo (impares) del zocalo del CC1101
Y_SM = 8.636          # fila de arriba del SuperMini (G0..5V); la de abajo (G21..G5) a + SM_ROW
comps = [
    socket1("U2A", "C3_SuperMini (fila abajo)", XS, Y_SM + SM_ROW, list(reversed(sm_R)), S8, "B"),
    socket1("U2B", "C3_SuperMini (fila arriba)", XS, Y_SM, list(reversed(sm_L)), S8, "T"),
    socket2x4_rot("U3", "E07-M1101D", X_CC, Y_CC, cc_pins, S24),
    cp_radial("C1", "100uF", 17.018, 3.048, "3V3", "GND"),   # al lado del CC1101, junto al borde derecho
]
if VARIANT == "C":
    # todo en linea: SuperMini con el USB a la izquierda, condensador en medio y el CC1101
    # a la derecha con el modulo (y el SMA) saliendo por el borde derecho.
    BX1, BY1 = 31.75, 18.288
    Y_T, Y_B = 1.524, 1.524 + SM_ROW
    X_CC = 27.686                 # columna de pines impares del CC1101
    Y_CC = 5.334                  # primera fila del zocalo (modulo de 15 mm centrado en vertical)
    comps = [
        socket1("U2A", "C3_SuperMini (fila arriba)", XS, Y_T, sm_R, S8, "T"),
        socket1("U2B", "C3_SuperMini (fila abajo)", XS, Y_B, sm_L, S8, "B"),
        socket2x4("U3", "E07-M1101D", X_CC, Y_CC, cc_pins, S24),
        cp_radial("C1", "100uF", 23.368, 8.128, "3V3", "GND", vertical=True),
    ]
if VARIANT == "D":
    # SuperMini con el USB a la izquierda, condensador libre en medio y el CC1101 al lado,
    # con el zocalo abajo y el modulo subiendo (antena arriba) por encima de la placa.
    BX1, BY1 = 39.116, 18.288
    Y_T, Y_B = 1.524, 1.524 + SM_ROW
    X_CC = 29.972                 # pin 1 del CC1101
    Y_CC = Y_B - 1.27             # fila de abajo (impares) del zocalo, algo por encima del borde para que pase la masa
    comps = [
        socket1("U2A", "C3_SuperMini (fila arriba)", XS, Y_T, sm_R, S8, "T"),
        socket1("U2B", "C3_SuperMini (fila abajo)", XS, Y_B, sm_L, S8, "B"),
        socket2x4_rot("U3", "E07-M1101D", X_CC, Y_CC, cc_pins, S24),
        cp_radial("C1", "100uF", 23.368, 8.128, "3V3", "GND", vertical=True),
    ]
if VARIANT == "X":
    # como la D, con XIAO ESP32-C6 girado (USB a la izquierda): la columna derecha (USB arriba)
    # pasa a ser la fila de arriba y la izquierda la de abajo, con el pin junto al USB a la izquierda.
    BX1, BY1 = 38.1, 18.288
    Y_T, Y_B = 1.524, 1.524 + SM_ROW
    X_CC = 28.956
    Y_CC = Y_B - 1.27
    comps = [
        socket1("U1A", "XIAO_ESP32-C6 (fila arriba)", XS, Y_T, xiao_R, S7, "T"),
        socket1("U1B", "XIAO_ESP32-C6 (fila abajo)", XS, Y_B, xiao_L, S7, "B"),
        socket2x4_rot("U3", "E07-M1101D", X_CC, Y_CC, cc_pins, S24),
        cp_radial("C1", "100uF", 22.352, 8.128, "3V3", "GND", vertical=True),
    ]
for c in comps:
    for p in c["pads"]:
        p["nid"] = NID[p["net"]] if p["net"] else 0
        p["solid"] = p["net"] == "GND"   # masa maciza (evita termicos sin radios en placa tan pequena)

# ------------------------------------------------------------------ router (rejilla, A*)
NX, NY = int(round(BX1 / G)), int(round(BY1 / G))
W, H = NX + 1, NY + 1
LAYERS = ["F.Cu", "B.Cu"]
NMASK = len(NETS) + 2   # 0 = sin red, len+1 = borde

def newmask():
    return bytearray(W * H)

def stamp_disc(arr, cx, cy, R):
    for i in range(max(0, int(math.floor((cx - R) / G))), min(NX, int(math.ceil((cx + R) / G))) + 1):
        for j in range(max(0, int(math.floor((cy - R) / G))), min(NY, int(math.ceil((cy + R) / G))) + 1):
            if (i * G - cx) ** 2 + (j * G - cy) ** 2 <= R * R + 1e-9:
                arr[i * H + j] = 1

def stamp_rect(arr, cx, cy, hw, hh):
    for i in range(max(0, int(math.floor((cx - hw) / G))), min(NX, int(math.ceil((cx + hw) / G))) + 1):
        for j in range(max(0, int(math.floor((cy - hh) / G))), min(NY, int(math.ceil((cy + hh) / G))) + 1):
            if abs(i * G - cx) <= hw + 1e-9 and abs(j * G - cy) <= hh + 1e-9:
                arr[i * H + j] = 1

def build_masks():
    m = {(l, n): newmask() for l in (0, 1) for n in range(NMASK)}
    extra = CLR + TW / 2
    for c in comps:
        for p in c["pads"]:
            for l in (0, 1):
                if p["rect"]:
                    stamp_rect(m[(l, p["nid"])], p["x"], p["y"], p["w"] / 2 + extra, p["h"] / 2 + extra)
                else:
                    stamp_disc(m[(l, p["nid"])], p["x"], p["y"], p["w"] / 2 + extra)
    for l in (0, 1):
        e = m[(l, NMASK - 1)]
        for i in range(W):
            for j in range(H):
                X, Y = i * G, j * G
                if X < BX0 + EDGE or X > BX1 - EDGE or Y < BY0 + EDGE or Y > BY1 - EDGE:
                    e[i * H + j] = 1
    return m

def blocked_for(masks, nid):
    out = []
    for l in (0, 1):
        b = newmask()
        for n in range(NMASK):
            if n != nid:
                src = masks[(l, n)]
                b = bytearray(x | y for x, y in zip(b, src))
        out.append(b)
    return out

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def astar(sources, tpos, tlayers, blk, bend=3, via_cost=30, limit=1_500_000):
    ti, tj = tpos
    goal = {(l, ti, tj) for l in tlayers}
    dist, par, heap = {}, {}, []
    for s in sources:
        st = (s[0], s[1], s[2], 4)
        dist[st] = 0
        heapq.heappush(heap, (abs(s[1] - ti) + abs(s[2] - tj), 0, st))
    n = 0
    free = lambda l, i, j: 0 <= i <= NX and 0 <= j <= NY and not blk[l][i * H + j]
    while heap:
        f_, g, st = heapq.heappop(heap)
        if dist.get(st, 1e18) < g:
            continue
        l, i, j, d = st
        if (l, i, j) in goal:
            path = []
            while st is not None:
                path.append(st[:3])
                st = par.get(st)
            return path[::-1]
        n += 1
        if n > limit:
            return None
        for nd, (di, dj) in enumerate(DIRS):
            ni, nj = i + di, j + dj
            if not free(l, ni, nj):
                continue
            ns = (l, ni, nj, nd)
            ng = g + 1 + (bend if (d != 4 and d != nd) else 0)
            if ng < dist.get(ns, 1e18):
                dist[ns] = ng
                par[ns] = st
                heapq.heappush(heap, (ng + abs(ni - ti) + abs(nj - tj), ng, ns))
        if free(0, i, j) and free(1, i, j) and all(free(0, i + a, j + b) and free(1, i + a, j + b) for a, b in DIRS):
            ns = (1 - l, i, j, 4)
            ng = g + via_cost
            if ng < dist.get(ns, 1e18):
                dist[ns] = ng
                par[ns] = st
                heapq.heappush(heap, (ng + abs(i - ti) + abs(j - tj), ng, ns))
    return None

def cellof(x, y):
    return int(round(x / G)), int(round(y / G))

def route_all(order):
    masks = build_masks()
    tracks, vias, failed = [], [], []
    for net in order:
        nid = NID[net]
        pads = [(c["ref"], p) for c in comps for p in c["pads"] if p["net"] == net]
        if len(pads) < 2:
            continue
        blk = blocked_for(masks, nid)
        p0 = pads[0][1]
        tree = {(l,) + cellof(p0["x"], p0["y"]) for l in (0, 1)}
        remaining = pads[1:]
        while remaining:
            ref, ti = min(remaining, key=lambda rp: min(abs(cellof(rp[1]["x"], rp[1]["y"])[0] - t[1]) +
                                                          abs(cellof(rp[1]["x"], rp[1]["y"])[1] - t[2]) for t in tree))
            remaining.remove((ref, ti))
            path = astar(list(tree), cellof(ti["x"], ti["y"]), (0, 1), blk)
            if path is None:
                failed.append((net, ref, ti["num"]))
                break
            prev = path[0]
            for cur in path[1:]:
                if cur[0] != prev[0]:
                    vias.append((prev[1] * G, prev[2] * G, nid))
                    for l in (0, 1):
                        stamp_disc(masks[(l, nid)], prev[1] * G, prev[2] * G, VIA_D / 2 + CLR + TW / 2)
                prev = cur
            for cell in path:
                stamp_disc(masks[(cell[0], nid)], cell[1] * G, cell[2] * G, TW + CLR)
                tree.add(cell)
            runs, start = [], path[0]
            for k in range(1, len(path)):
                a, b = path[k - 1], path[k]
                if b[0] != a[0]:
                    if a != start:
                        runs.append((start, a))
                    start = b
                    continue
                if k + 1 < len(path):
                    c = path[k + 1]
                    if c[0] == b[0] and (c[1] - b[1], c[2] - b[2]) == (b[1] - a[1], b[2] - a[2]):
                        continue
                if b != start:
                    runs.append((start, b))
                start = b
            for a, b in runs:
                tracks.append((a[1] * G, a[2] * G, b[1] * G, b[2] * G, a[0], nid))
    return tracks, vias, failed

def try_routing():
    import random
    base = ["3V3", "SCK", "MOSI", "MISO", "CS", "GDO0"]
    rnd = random.Random(7)
    best = None
    for attempt in range(20):
        order = (base[:] if attempt == 0 else rnd.sample(base, len(base))) + ["GND"]
        tr, vi, fl = route_all(order)
        print(f"intento {attempt}: orden={order} pistas={len(tr)} vias={len(vi)} fallos={fl}", flush=True)
        if best is None or (len(fl), len(vi)) < (len(best[2]), len(best[1])):
            best = (tr, vi, fl, order)
        if not fl and not vi:
            break
    return best

# ------------------------------------------------------------------ escritura PCB
def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"

def eff(size=1.0, th=0.15, just=None, hide=False):
    s = f"(effects (font (size {size} {size}) (thickness {th}))"
    if just:
        s += f" (justify {just})"
    if hide:
        s += " (hide yes)"
    return s + ")"

def pcb_text(tracks, vias):
    L = []
    A = L.append
    A('(kicad_pcb (version 20240108) (generator "pcbnew") (generator_version "8.0")')
    A('  (general (thickness 1.6) (legacy_teardrops no))')
    A('  (paper "A4")')
    A('  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")'
      ' (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")'
      ' (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")'
      ' (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2") (44 "Edge.Cuts" user) (45 "Margin" user)'
      ' (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))')
    A('  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))')
    A('  (net 0 "")')
    for n in NETS:
        A(f'  (net {NID[n]} "{n}")')
    for c in comps:
        x, y = c["x"] + OX, c["y"] + OY
        A(f'  (footprint "{c["fpid"]}" (layer "F.Cu") (uuid "{U()}") (at {f(x)} {f(y)})')
        A(f'    (descr "{c["value"]}") (tags "rf cc1101")')
        A(f'    (property "Reference" "{c["ref"]}" (at 0 0 0) (layer "F.Fab") (uuid "{U()}") {eff(0.8, 0.12)})')
        A(f'    (property "Value" "{c["value"]}" (at 0 1 0) (layer "F.Fab") (uuid "{U()}") {eff(0.8, 0.12)})')
        A(f'    (property "Footprint" "{c["fpid"]}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (path "/{c["sym"]}")')
        A(f'    (sheetname "Root") (sheetfile "{NAME}.kicad_sch")')
        A('    (attr through_hole)')
        if c.get("circle"):
            cx, cy, r = c["circle"]
            A(f'    (fp_circle (center {f(cx)} {f(cy)}) (end {f(cx + r)} {f(cy)}) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS") (uuid "{U()}"))')
            A(f'    (fp_text user "+" (at {f(c["plus"][0])} {f(c["plus"][1])} 0) (layer "F.SilkS") (uuid "{U()}") {eff(1.0, 0.15)})')
        for p in c["pads"]:
            dx, dy = p["x"] - c["x"], p["y"] - c["y"]
            net = f' (net {p["nid"]} "{p["net"]}")' if p["nid"] else ""
            if p.get("solid"):
                net = " (zone_connect 2)" + net
            shape = "rect" if p["rect"] else "circle"
            A(f'    (pad "{p["num"]}" thru_hole {shape} (at {f(dx)} {f(dy)}) (size {p["w"]} {p["h"]}) (drill {p["drill"]})'
              f' (layers "*.Cu" "*.Mask") (remove_unused_layers no){net} (pintype "passive") (uuid "{U()}"))')
        A('  )')
    x0, y0, x1, y1 = BX0 + OX, BY0 + OY, BX1 + OX, BY1 + OY
    A(f'  (gr_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{U()}"))')
    def outline(xa, ya, xb, yb, label):
        A(f'  (gr_rect (start {f(xa + OX)} {f(ya + OY)}) (end {f(xb + OX)} {f(yb + OY)}) (stroke (width 0.15) (type dash)) (fill none) (layer "Dwgs.User") (uuid "{U()}"))')
        A(f'  (gr_text "{label}" (at {f((xa + xb) / 2 + OX)} {f((ya + yb) / 2 + OY)}) (layer "Dwgs.User") (uuid "{U()}") {eff(1.0)})')
    if VARIANT == "C":
        outline(XS - 3.36, Y_T - 1.38, XS + 7 * 2.54 + 1.36, Y_B + 1.38, "C3 SuperMini (USB a la izquierda)")
        outline(X_CC - 1.4, Y_CC - 3.69, X_CC + 27.2, Y_CC + 11.31, "E07-M1101D (SMA a la derecha)")
    elif VARIANT == "X":
        outline(XS - 2.9, Y_T - 1.28, XS + 6 * 2.54 + 2.9, Y_B + 1.28, "XIAO ESP32-C6 (USB a la izquierda)")
        outline(X_CC - 3.69, Y_CC - 27.2, X_CC + 11.31, Y_CC + 1.4, "E07-M1101D (antena arriba)")
    elif VARIANT == "D":
        outline(XS - 3.36, Y_T - 1.38, XS + 7 * 2.54 + 1.36, Y_B + 1.38, "C3 SuperMini (USB a la izquierda)")
        outline(X_CC - 3.69, Y_CC - 27.2, X_CC + 11.31, Y_CC + 1.4, "E07-M1101D (antena arriba)")
    else:
        outline(XS - 1.36, Y_SM - 1.38, XS + 7 * 2.54 + 3.36, Y_SM + SM_ROW + 1.38, "C3 SuperMini (USB a la derecha)")
        outline(X_CC - 3.69, Y_CC - 27.2, X_CC + 11.31, Y_CC + 1.4, "E07-M1101D (antena arriba)")
    # serigrafia: nombres de pin en la cara de atras (delante queda tapado por los modulos)
    for c in comps:
        if c["ref"] == "C1":
            continue
        for k, p in enumerate(c["pads"]):
            if p["side"] in ("A", "L", "R") or (VARIANT in ("D", "X") and p["side"] == "D"):
                continue   # CC1101 sin texto donde no cabe (el pin 1 es el cuadrado)
            dx, dy, ang = {"T": (0, 2.3, 90), "B": (0, -2.3, 90), "D": (0, 1.45 if k % 4 == 0 else 2.45, 0)}[p["side"]]
            A(f'  (gr_text "{p["name"]}" (at {f(p["x"] + dx + OX)} {f(p["y"] + dy + OY)} {ang}) (layer "B.SilkS") (uuid "{U()}") {eff(0.8, 0.15, "mirror")})')
    if VARIANT in ("C", "D", "X"):
        ym = BY1 / 2
        t_title, t_usb, t_cap = (10.4, ym), (2.6, ym), (22.352 if VARIANT == "X" else 23.368, 12.6)
    else:
        ym = Y_SM + SM_ROW / 2
        t_title, t_usb, t_cap = (7.5, ym), (19.2, ym), (18.018, 6.3)
    A(f'  (gr_text "{"CC1101 v2 XIAO" if VARIANT == "X" else "CC1101 v2"}" (at {f(t_title[0] + OX)} {f(t_title[1] + OY)}) (layer "B.SilkS") (uuid "{U()}") {eff(0.8, 0.15, "mirror")})')
    A(f'  (gr_text "USB" (at {f(t_usb[0] + OX)} {f(t_usb[1] + OY)} 90) (layer "F.SilkS") (uuid "{U()}") {eff(0.8, 0.15)})')
    A(f'  (gr_text "100uF" (at {f(t_cap[0] + OX)} {f(t_cap[1] + OY)}) (layer "B.SilkS") (uuid "{U()}") {eff(0.8, 0.15, "mirror")})')
    for xa, ya, xb, yb, l, nid in tracks:
        A(f'  (segment (start {f(xa + OX)} {f(ya + OY)}) (end {f(xb + OX)} {f(yb + OY)}) (width {TW}) (layer "{LAYERS[l]}") (net {nid}) (uuid "{U()}"))')
    for x, y, nid in vias:
        A(f'  (via (at {f(x + OX)} {f(y + OY)}) (size {VIA_D}) (drill {VIA_DR}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{U()}"))')
    m = 0.3
    for lay in LAYERS:
        pts = f'(xy {f(x0 + m)} {f(y0 + m)}) (xy {f(x1 - m)} {f(y0 + m)}) (xy {f(x1 - m)} {f(y1 - m)}) (xy {f(x0 + m)} {f(y1 - m)})'
        A(f'  (zone (net {NID["GND"]}) (net_name "GND") (layer "{lay}") (uuid "{U()}") (hatch edge 0.5)'
          f' (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no)'
          f' (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts {pts})))')
    A(')')
    return "\n".join(L)

# ------------------------------------------------------------------ esquema
def sch_text():
    L = []
    A = L.append
    A(f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid "{ROOT}") (paper "A4")')
    A('  (lib_symbols')
    for c in comps:
        n = len(c["pads"])
        top = (n - 1) * 1.27 + 1.27
        A(f'    (symbol "{NAME}:{c["ref"]}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)')
        A(f'      (property "Reference" "{c["ref"][0]}" (at 0 {f(top + 2.54)} 0) {eff(1.27)})')
        A(f'      (property "Value" "{c["value"]}" (at 0 {f(-top - 2.54)} 0) {eff(1.27)})')
        A(f'      (property "Footprint" "" (at 0 0 0) {eff(1.27, hide=True)})')
        A(f'      (property "Datasheet" "" (at 0 0 0) {eff(1.27, hide=True)})')
        A(f'      (symbol "{c["ref"]}_1_1"')
        A(f'        (rectangle (start -5.08 {f(top)}) (end 5.08 {f(-top)}) (stroke (width 0.254) (type default)) (fill (type background)))')
        for i, p in enumerate(c["pads"]):
            py = (n - 1) * 1.27 - i * 2.54
            A(f'        (pin passive line (at -7.62 {f(py)} 0) (length 2.54) (name "{p["name"] or "NC"}" {eff(1.0)}) (number "{p["num"]}" {eff(1.0)}))')
        A('      )')
        A('    )')
    A('  )')
    pos = {"U2A": (50.8, 60.96), "U2B": (101.6, 60.96), "U1A": (50.8, 60.96), "U1B": (101.6, 60.96), "U3": (152.4, 60.96), "C1": (203.2, 60.96)}
    for c in comps:
        sx, sy = pos[c["ref"]]
        n = len(c["pads"])
        top = (n - 1) * 1.27 + 1.27
        A(f'  (symbol (lib_id "{NAME}:{c["ref"]}") (at {f(sx)} {f(sy)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{c["sym"]}")')
        A(f'    (property "Reference" "{c["ref"]}" (at {f(sx)} {f(sy - top - 2.54)} 0) {eff(1.27)})')
        A(f'    (property "Value" "{c["value"]}" (at {f(sx)} {f(sy + top + 2.54)} 0) {eff(1.27)})')
        A(f'    (property "Footprint" "{c["fpid"]}" (at {f(sx)} {f(sy)} 0) {eff(1.27, hide=True)})')
        A(f'    (property "Datasheet" "" (at {f(sx)} {f(sy)} 0) {eff(1.27, hide=True)})')
        for p in c["pads"]:
            A(f'    (pin "{p["num"]}" (uuid "{U()}"))')
        A(f'    (instances (project "{NAME}" (path "/{ROOT}" (reference "{c["ref"]}") (unit 1))))')
        A('  )')
        for i, p in enumerate(c["pads"]):
            py = sy - ((n - 1) * 1.27 - i * 2.54)
            px = sx - 7.62
            if p["net"]:
                A(f'  (global_label "{p["net"]}" (shape passive) (at {f(px)} {f(py)} 180) (fields_autoplaced yes) {eff(1.27, just="right")} (uuid "{U()}")')
                A(f'    (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {f(px)} {f(py)} 0) {eff(1.27, hide=True)}))')
            else:
                A(f'  (no_connect (at {f(px)} {f(py)}) (uuid "{U()}"))')
    A('  (sheet_instances (path "/" (page "1")))')
    A(')')
    return "\n".join(L)

def pro_text():
    return ('{"meta":{"filename":"%s.kicad_pro","version":1},"net_settings":{"classes":[{"name":"Default",'
            '"clearance":0.2,"track_width":0.3,"via_diameter":0.8,"via_drill":0.4,"wire_width":6,"bus_width":12,'
            '"line_style":0,"pcb_color":"rgba(0, 0, 0, 0.000)","schematic_color":"rgba(0, 0, 0, 0.000)",'
            '"diff_pair_gap":0.25,"diff_pair_via_gap":0.25,"diff_pair_width":0.2,"microvia_diameter":0.3,'
            '"microvia_drill":0.1}],"meta":{"version":3},"net_colors":null,"netclass_assignments":null,'
            '"netclass_patterns":[]},"sheets":[["%s","Root"]],"text_variables":{}}' % (NAME, ROOT))

def main():
    os.makedirs(OUT, exist_ok=True)
    tracks, vias, failed, order = try_routing()
    open(f"{OUT}/{NAME}.kicad_pcb", "w").write(pcb_text(tracks, vias))
    open(f"{OUT}/{NAME}.kicad_sch", "w").write(sch_text())
    open(f"{OUT}/{NAME}.kicad_pro", "w").write(pro_text())
    print("orden:", order, "pistas:", len(tracks), "vias:", len(vias), "fallos:", failed)

if __name__ == "__main__":
    main()
