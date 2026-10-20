#!/usr/bin/env python3
"""Genera un proyecto KiCad 8/9 (rf_cc1101.kicad_pro / _pcb / _sch).

Placa: zocalos para XIAO ESP32-C6 y ESP32-C3 SuperMini (solo se monta UNO)
+ zocalo 2x4 para el modulo E07-M1101D + cabecera I2C + 2 condensadores.
Todo es parametrico: cambia los valores de abajo y vuelve a ejecutar.
"""
import heapq, math, os, random, sys, uuid
import numpy as np

# ------------------------------------------------------------------ parametros
MCU_ROW = 15.24      # distancia entre filas de pines del XIAO (0.6")
SM_ROW = 15.24       # distancia entre filas de pines del C3 SuperMini  <-- MIDELO
CC_ROW = 2.54        # separacion entre filas del zocalo del CC1101 (2x4 estandar)
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
NAME = "rf_cc1101"

G = 0.254            # rejilla del router (mm)
TW, CLR = 0.3, 0.2   # ancho de pista, holgura
VIA_D, VIA_DR = 0.8, 0.4
PAD_D, DRILL = 1.7, 1.0
BX0, BY0, BX1, BY1 = 0.0, 5.08, 58.42, 58.42   # contorno (coord. locales)
OX, OY = 76.2, 50.8  # desplazamiento para colocar la placa en la hoja
EDGE = 0.9           # margen pistas-borde

NETS = ["GND", "3V3", "SCK", "MISO", "MOSI", "CS", "GDO0", "GDO2", "SDA", "SCL"]
NID = {n: i + 1 for i, n in enumerate(NETS)}
U = lambda: str(uuid.uuid4())
ROOT = U()

# ------------------------------------------------------------------ componentes
def socket1(ref, value, x, y, pins, fpid):
    pads = []
    for i, (name, net) in enumerate(pins):
        pads.append(dict(num=str(i + 1), name=name, net=net, x=x, y=y + i * 2.54,
                         kind="thru", rect=(i == 0), w=PAD_D, h=PAD_D, side="L"))
    return dict(ref=ref, value=value, fpid=fpid, x=x, y=y, pads=pads, sym=U())

def socket2x4(ref, value, x, y, pins, fpid):
    pads = []
    for n, (name, net) in enumerate(pins):
        c, r = n % 2, n // 2
        pads.append(dict(num=str(n + 1), name=name, net=net, x=x + c * CC_ROW, y=y + r * 2.54,
                         kind="thru", rect=(n == 0), w=PAD_D, h=PAD_D, side="L" if c == 0 else "R"))
    return dict(ref=ref, value=value, fpid=fpid, x=x, y=y, pads=pads, sym=U())

def cap(ref, value, x, y, net1, net2):
    pads = [dict(num="1", name="1", net=net1, x=x - 0.95, y=y, kind="smd", rect=False, w=1.0, h=1.45, side="L"),
            dict(num="2", name="2", net=net2, x=x + 0.95, y=y, kind="smd", rect=False, w=1.0, h=1.45, side="R")]
    return dict(ref=ref, value=value, fpid="Capacitor_SMD:C_0805_2012Metric", x=x, y=y, pads=pads, sym=U(), silk=False)

S7 = "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical"
S8 = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"
S24 = "Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical"
H4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"

# XIAO ESP32-C6 (USB arriba). GDO2 va a D0 porque GPIO3 NO sale a los pines.
xiao_L = [("D0 G0", "GDO2"), ("D1 G1", "CS"), ("D2 G2", "GDO0"), ("D3 G21", None),
          ("D4 G22", None), ("D5 G23", "SDA"), ("D6 G16", "SCL")]
xiao_R = [("5V", None), ("GND", "GND"), ("3V3", "3V3"), ("D10 G18", "MOSI"),
          ("D9 G20", "MISO"), ("D8 G19", "SCK"), ("D7 G17", None)]

# ESP32-C3 SuperMini girado 180 grados (USB hacia abajo)
sm_L = [("5V", None), ("GND", "GND"), ("3V3", "3V3"), ("G4", "SCK"), ("G3", "GDO0"),
        ("G2", None), ("G1", "SCL"), ("G0", "SDA")]
sm_R = [("G5", "MISO"), ("G6", "MOSI"), ("G7", "CS"), ("G8", None), ("G9", None),
        ("G10", "GDO2"), ("G20", None), ("G21", None)]

# E07-M1101D (misma disposicion que NRF24L01: GND VCC GDO0 CSN SCK MOSI MISO GDO2)
cc_pins = [("GND", "GND"), ("VCC", "3V3"), ("GDO0", "GDO0"), ("CSN", "CS"),
           ("SCK", "SCK"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("GDO2", "GDO2")]

X1 = 7.62
comps = [
    socket1("U1A", "XIAO_ESP32-C6 (izq)", X1, 10.16, xiao_L, S7),
    socket1("U1B", "XIAO_ESP32-C6 (der)", X1 + MCU_ROW, 10.16, xiao_R, S7),
    socket1("U2A", "C3_SuperMini girado (izq)", X1, 35.56, list(reversed(sm_R)), S8),
    socket1("U2B", "C3_SuperMini girado (der)", X1 + SM_ROW, 35.56, list(reversed(sm_L)), S8),
    socket2x4("U3", "E07-M1101D", 50.8, 27.94, cc_pins, S24),
    socket1("J1", "I2C sensor", 34.29, 10.16, [("3V3", "3V3"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL")], H4),
    cap("C1", "10uF", 49.53, 22.86, "3V3", "GND"),
    cap("C2", "100nF", 49.53, 20.32, "3V3", "GND"),
]
for c in comps:
    c.setdefault("silk", True)
    for p in c["pads"]:
        p["nid"] = NID[p["net"]] if p["net"] else 0
        p["solid"] = bool(p["net"] == "GND" and (c["ref"] in ("C1", "C2") or c["ref"] == "U3"))

# ------------------------------------------------------------------ router
NX, NY = int(round(BX1 / G)), int(round(BY1 / G))
LAYERS = ["F.Cu", "B.Cu"]

def stamp_disc(arr, cx, cy, R):
    i0, i1 = max(0, int(math.floor((cx - R) / G))), min(NX, int(math.ceil((cx + R) / G)))
    j0, j1 = max(0, int(math.floor((cy - R) / G))), min(NY, int(math.ceil((cy + R) / G)))
    ii, jj = np.ogrid[i0:i1 + 1, j0:j1 + 1]
    arr[i0:i1 + 1, j0:j1 + 1] |= ((ii * G - cx) ** 2 + (jj * G - cy) ** 2) <= R * R + 1e-9

def stamp_rect(arr, cx, cy, hw, hh):
    i0, i1 = max(0, int(math.floor((cx - hw) / G))), min(NX, int(math.ceil((cx + hw) / G)))
    j0, j1 = max(0, int(math.floor((cy - hh) / G))), min(NY, int(math.ceil((cy + hh) / G)))
    ii, jj = np.ogrid[i0:i1 + 1, j0:j1 + 1]
    arr[i0:i1 + 1, j0:j1 + 1] |= (np.abs(ii * G - cx) <= hw + 1e-9) & (np.abs(jj * G - cy) <= hh + 1e-9)

def build_masks():
    m = {(l, n): np.zeros((NX + 1, NY + 1), bool) for l in (0, 1) for n in range(len(NETS) + 2)}
    extra = CLR + TW / 2
    for c in comps:
        for p in c["pads"]:
            layers = (0, 1) if p["kind"] == "thru" else (0,)
            for l in layers:
                if p["rect"] or p["kind"] == "smd":
                    stamp_rect(m[(l, p["nid"])], p["x"], p["y"], p["w"] / 2 + extra, p["h"] / 2 + extra)
                else:
                    stamp_disc(m[(l, p["nid"])], p["x"], p["y"], p["w"] / 2 + extra)
    # borde: bloqueado para todos (red "borde" = id len+1 nunca es propia)
    edge = np.zeros((NX + 1, NY + 1), bool)
    ii, jj = np.ogrid[0:NX + 1, 0:NY + 1]
    X, Y = ii * G, jj * G
    edge |= (X < BX0 + EDGE) | (X > BX1 - EDGE) | (Y < BY0 + EDGE) | (Y > BY1 - EDGE)
    for l in (0, 1):
        m[(l, len(NETS) + 1)] |= edge
    return m

def blocked_for(masks, nid):
    out = []
    for l in (0, 1):
        b = np.zeros((NX + 1, NY + 1), bool)
        for n in range(len(NETS) + 2):
            if n != nid:
                b |= masks[(l, n)]
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
    while heap:
        f, g, st = heapq.heappop(heap)
        if dist.get(st, 1e18) < g:
            continue
        l, i, j, d = st
        if (l, i, j) in goal:
            path = []
            while st in par or st is not None:
                path.append(st[:3])
                st = par.get(st)
                if st is None:
                    break
            return path[::-1]
        n += 1
        if n > limit:
            return None
        for nd, (di, dj) in enumerate(DIRS):
            ni, nj = i + di, j + dj
            if ni < 0 or nj < 0 or ni > NX or nj > NY or blk[l][ni, nj]:
                continue
            cost = 1 + (bend if (d != 4 and d != nd) else 0)
            ns = (l, ni, nj, nd)
            ng = g + cost
            if ng < dist.get(ns, 1e18):
                dist[ns] = ng
                par[ns] = st
                heapq.heappush(heap, (ng + abs(ni - ti) + abs(nj - tj), ng, ns))
        # via
        ol = 1 - l
        if (not blk[0][i, j] and not blk[1][i, j] and
                all(0 <= i + a <= NX and 0 <= j + b <= NY and not blk[0][i + a, j + b] and not blk[1][i + a, j + b]
                    for a, b in DIRS)):
            ns = (ol, i, j, 4)
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
        pads = [p for c in comps for p in c["pads"] if p["net"] == net]
        if len(pads) < 2:
            continue
        blk = blocked_for(masks, nid)
        def pl(p): return (0, 1) if p["kind"] == "thru" else (0,)
        p0 = pads[0]
        tree = {(l,) + cellof(p0["x"], p0["y"]) for l in pl(p0)}
        remaining = pads[1:]
        ok = True
        while remaining:
            ti = sorted(remaining, key=lambda p: min(abs(cellof(p["x"], p["y"])[0] - t[1]) +
                                                      abs(cellof(p["x"], p["y"])[1] - t[2]) for t in tree))[0]
            remaining.remove(ti)
            path = astar(list(tree), cellof(ti["x"], ti["y"]), pl(ti), blk)
            if path is None:
                ok = False
                failed.append((net, ti["ref"] if "ref" in ti else ti["num"]))
                break
            # segmentos
            seg_start = path[0]
            prev = path[0]
            for cur in path[1:]:
                if cur[0] != prev[0]:  # via
                    vias.append((prev[1] * G, prev[2] * G, nid))
                    stamp_disc(masks[(0, nid)], prev[1] * G, prev[2] * G, VIA_D / 2 + CLR + TW / 2)
                    stamp_disc(masks[(1, nid)], prev[1] * G, prev[2] * G, VIA_D / 2 + CLR + TW / 2)
                prev = cur
            for cell in path:
                stamp_disc(masks[(cell[0], nid)], cell[1] * G, cell[2] * G, TW + CLR)
                tree.add(cell)
            # unir en segmentos rectos
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
        if not ok:
            pass
    return tracks, vias, failed

def try_routing():
    base = ["3V3", "SCK", "MOSI", "MISO", "CS", "GDO0", "GDO2", "SDA", "SCL"]
    last = ["GND"]
    rnd = random.Random(7)
    best = None
    for attempt in range(20):
        order = (base[:] if attempt == 0 else rnd.sample(base, len(base))) + last
        tr, vi, fl = route_all(order)
        print(f"intento {attempt}: orden={order} fallos={fl}", flush=True)
        if best is None or len(fl) < len(best[2]):
            best = (tr, vi, fl, order)
        if not fl:
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
        A(f'    (property "Reference" "{c["ref"]}" (at 0 -2.6 0) (layer "{"F.SilkS" if c["silk"] else "F.Fab"}") (uuid "{U()}") {eff(1.0)})')
        A(f'    (property "Value" "{c["value"]}" (at 0 -4 0) (layer "F.Fab") (uuid "{U()}") {eff(1.0)})')
        A(f'    (property "Footprint" "{c["fpid"]}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff(1.27)})')
        A(f'    (path "/{c["sym"]}")')
        A(f'    (sheetname "Root") (sheetfile "{NAME}.kicad_sch")')
        A('    (attr through_hole)' if c["pads"][0]["kind"] == "thru" else '    (attr smd)')
        for p in c["pads"]:
            dx, dy = p["x"] - c["x"], p["y"] - c["y"]
            net = f' (net {p["nid"]} "{p["net"]}")' if p["nid"] else ""
            if p.get("solid"):
                net = " (zone_connect 2)" + net
            if p["kind"] == "thru":
                shape = "rect" if p["rect"] else "circle"
                A(f'    (pad "{p["num"]}" thru_hole {shape} (at {f(dx)} {f(dy)}) (size {p["w"]} {p["h"]}) (drill {DRILL})'
                  f' (layers "*.Cu" "*.Mask") (remove_unused_layers no){net} (pintype "passive") (uuid "{U()}"))')
            else:
                A(f'    (pad "{p["num"]}" smd roundrect (at {f(dx)} {f(dy)}) (size {p["w"]} {p["h"]})'
                  f' (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25){net} (pintype "passive") (uuid "{U()}"))')
        A('  )')
    # contorno
    x0, y0, x1, y1 = BX0 + OX, BY0 + OY, BX1 + OX, BY1 + OY
    A(f'  (gr_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{U()}"))')
    # siluetas orientativas de las placas (capa Dwgs.User)
    def outline(xa, ya, xb, yb, label):
        A(f'  (gr_rect (start {f(xa + OX)} {f(ya + OY)}) (end {f(xb + OX)} {f(yb + OY)}) (stroke (width 0.15) (type dash)) (fill none) (layer "Dwgs.User") (uuid "{U()}"))')
        A(f'  (gr_text "{label}" (at {f((xa + xb) / 2 + OX)} {f((ya + yb) / 2 + OY)}) (layer "Dwgs.User") (uuid "{U()}") {eff(1.0)})')
    cx = X1 + MCU_ROW / 2
    outline(cx - 8.9, 8.6, cx + 8.9, 29.6, "XIAO C6 (orientativo)")
    cs = X1 + SM_ROW / 2
    outline(cs - 9.0, 34.2, cs + 9.0, 56.7, "C3 SuperMini (USB abajo)")
    outline(49.4, 24.25, 78.0, 39.25, "E07-M1101D")
    # etiquetas de serigrafia
    for c in comps:
        if not c["silk"]:
            continue
        for p in c["pads"]:
            if not p["name"]:
                continue
            if p["side"] == "L":
                A(f'  (gr_text "{p["name"]}" (at {f(p["x"] - 1.3 + OX)} {f(p["y"] + OY)}) (layer "F.SilkS") (uuid "{U()}") {eff(0.8, 0.12, "right")})')
            else:
                A(f'  (gr_text "{p["name"]}" (at {f(p["x"] + 1.3 + OX)} {f(p["y"] + OY)}) (layer "F.SilkS") (uuid "{U()}") {eff(0.8, 0.12, "left")})')
    A(f'  (gr_text "RF CC1101 · XIAO C6 / C3 SuperMini" (at {f(40 + OX)} {f(55.5 + OY)}) (layer "F.SilkS") (uuid "{U()}") {eff(0.9, 0.13)})')
    # pistas
    for xa, ya, xb, yb, l, nid in tracks:
        A(f'  (segment (start {f(xa + OX)} {f(ya + OY)}) (end {f(xb + OX)} {f(yb + OY)}) (width {TW}) (layer "{LAYERS[l]}") (net {nid}) (uuid "{U()}"))')
    for x, y, nid in vias:
        A(f'  (via (at {f(x + OX)} {f(y + OY)}) (size {VIA_D}) (drill {VIA_DR}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{U()}"))')
    # zonas GND (ambas caras)
    m = 0.5
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
    pos = {"U1A": (50.8, 45.72), "U1B": (101.6, 45.72), "U2A": (50.8, 106.68), "U2B": (101.6, 106.68),
           "U3": (177.8, 45.72), "J1": (177.8, 106.68), "C1": (228.6, 45.72), "C2": (228.6, 76.2)}
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
    import json
    json.dump(dict(tracks=tracks, vias=vias, failed=failed), open("route.json", "w"))
    print("pistas:", len(tracks), "vias:", len(vias), "fallos:", failed)

if __name__ == "__main__":
    main()
