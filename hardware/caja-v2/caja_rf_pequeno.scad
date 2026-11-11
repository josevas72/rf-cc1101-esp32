// =====================================================================
//  Caja RF pequeño (placa v2 D: ESP32-C3 SuperMini + CC1101 + 100 uF)
//  Caja baja de una pieza abierta por arriba + tapa superior.
//  La tapa lleva el orificio del SMA: la tuerca de la antena aprieta el
//  módulo contra la tapa y, a la vez, cierra la caja.
//
//  Ejes: X de izquierda a derecha, Y de delante (0) hacia el fondo,
//        Z de abajo arriba. Medidas en mm.
//  Uso: part = "caja" | "tapa" | "ambas" | "montaje"
// =====================================================================

part = "ambas";

/* ---------- conjunto medido (placa + módulos + condensador) ---------- */
conj_x = 43;          // largo
conj_y = 16;          // fondo
conj_z = 32;          // alto: del apoyo en el suelo a la base de la rosca del SMA
holgura = 0.5;        // por lado, en largo y fondo (v3: vuelta a 0,5; con 1,75 el conjunto bailaba)
holgura_z = 0.5;      // encima del conjunto (no cambia: la rosca del SMA tiene que asomar)

/* ---------- USB-C (lado corto izquierdo, en vertical) ---------- */
usb_z_centro = 9;     // altura del centro sobre el apoyo del conjunto (v3: +3 mm, antes 6)
usb_desde_fondo = 4;  // centro, medido desde el fondo del conjunto
usb_paso_alto = 11;   // hueco que atraviesa la pared (v3: más grande, antes 9,6)
usb_paso_ancho = 5.0; // (v3: antes 4,0)
usb_rebaje_alto = 14;    // rebaje exterior para la funda del cable (v3: antes 12,5)
usb_rebaje_ancho = 8.0;  // (v3: antes 7,0)
usb_pared_restante = 0.8; // pared que queda en el fondo del rebaje

/* ---------- antena (sale por la tapa) ---------- */
ant_d = 7;            // orificio para la rosca SMA (1/4")
ant_desde_dcha = 7;   // centro, desde el lado derecho del conjunto (v2: 2 mm más a la izquierda)
ant_desde_frente = 5; // centro, desde el frente del conjunto
ant_largo = 47;       // solo para la vista "montaje"

/* ---------- caja ---------- */
pared = 2;
suelo = 2;
radio = 3;            // esquinas verticales
chaflan = 0.8;        // borde inferior de la caja y superior de la tapa
tapa_grosor = 2;
falda_alto = 4;       // v3: la tapa abraza la caja POR FUERA (antes labio interior); alto que baja por la pared
falda_pared = 1.5;    // grosor de la falda exterior de la tapa
ajuste = 0.05;        // holgura de la tapa sobre la pared exterior (v4: con 0,15 por fuera iba algo floja)

/* ---------- detalles ---------- */
ventilacion = true;   // ranuras en la pared del fondo
icono = true;         // onda y "RF" grabados en el frente
pies = true;          // rebajes para 4 pies de goma
pie_d = 8.5;
pie_prof = 1;
grabado = 0.6;

$fn = 64;

/* ---------- medidas derivadas ---------- */
int_x = conj_x + 2 * holgura;
int_y = conj_y + 2 * holgura;
int_z = conj_z + holgura_z;                 // del suelo interior a la cara de abajo de la tapa
ext_x = int_x + 2 * pared;
ext_y = int_y + 2 * pared;
caja_z = suelo + int_z;

usb_y = pared + holgura + conj_y - usb_desde_fondo;   // desde el frente exterior
usb_z = suelo + usb_z_centro;
ant_x = pared + holgura + conj_x - ant_desde_dcha;
ant_y = pared + holgura + ant_desde_frente;

echo(str("Caja exterior: ", ext_x, " x ", ext_y, " x ", caja_z + tapa_grosor, " mm (con tapa)"));

/* ---------- utilidades ---------- */
module rect_redondo(x, y, h, r) {
    r2 = max(r, 0.01);
    hull() for (i = [r2, x - r2], j = [r2, y - r2])
        translate([i, j, 0]) cylinder(r = r2, h = h);
}

// rectángulo redondeado con chaflán abajo (abajo = true) o arriba
module bloque(x, y, h, r, c, abajo = true) {
    hull() for (i = [r, x - r], j = [r, y - r]) translate([i, j, 0]) {
        if (abajo) {
            cylinder(r1 = r - c, r2 = r, h = c);
            translate([0, 0, c]) cylinder(r = r, h = h - c);
        } else {
            cylinder(r = r, h = h - c);
            translate([0, 0, h - c]) cylinder(r1 = r, r2 = r - c, h = c);
        }
    }
}

module ranura(largo, ancho, alto) {   // ranura de extremos redondos, en vertical (Z)
    hull() {
        translate([0, 0, ancho / 2]) rotate([90, 0, 0]) cylinder(d = ancho, h = alto, center = true);
        translate([0, 0, largo - ancho / 2]) rotate([90, 0, 0]) cylinder(d = ancho, h = alto, center = true);
    }
}

/* ---------- caja ---------- */
module caja() {
    difference() {
        bloque(ext_x, ext_y, caja_z, radio, chaflan, abajo = true);
        // hueco interior
        translate([pared, pared, suelo]) rect_redondo(int_x, int_y, int_z + 1, radio - pared);
        // USB: paso por la pared y rebaje exterior con chaflán
        translate([-1, usb_y - usb_paso_ancho / 2, usb_z - usb_paso_alto / 2])
            cube([pared + 2, usb_paso_ancho, usb_paso_alto]);
        hull() {
            translate([-1, usb_y - usb_rebaje_ancho / 2 - 0.6, usb_z - usb_rebaje_alto / 2 - 0.6])
                cube([1.01, usb_rebaje_ancho + 1.2, usb_rebaje_alto + 1.2]);
            translate([pared - usb_pared_restante - 0.01, usb_y - usb_rebaje_ancho / 2, usb_z - usb_rebaje_alto / 2])
                cube([0.01, usb_rebaje_ancho, usb_rebaje_alto]);
        }
        // ventilación en el fondo
        if (ventilacion)
            for (i = [0 : 5]) translate([ext_x / 2 - 12.5 + i * 5, ext_y - pared / 2, suelo + 8])
                ranura(int_z - 14, 2, pared + 2);
        // onda y "RF" grabados en el frente
        if (icono) translate([ext_x / 2, grabado - 0.01, caja_z / 2]) rotate([90, 0, 0]) frente();
        // pies
        if (pies) for (i = [pie_d / 2 + 2.5, ext_x - pie_d / 2 - 2.5], j = [pie_d / 2 + 2.5, ext_y - pie_d / 2 - 2.5])
            translate([i, j, -0.01]) cylinder(d = pie_d, h = pie_prof + 0.01);
    }
}

module frente() {   // relieve en el plano XY, se graba en la cara frontal
    linear_extrude(grabado + 0.02) {
        translate([-9, -1.5]) text("RF", size = 7, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
        for (k = [1 : 3]) translate([4, -1.5])
            intersection() {   // arcos de onda de -45 a 45 grados
                difference() {
                    circle(r = 2.2 + k * 2.6);
                    circle(r = 2.2 + k * 2.6 - 1);
                }
                polygon([[0, 0], [20, 20], [20, -20]]);
            }
        translate([4, -1.5]) circle(r = 1.4);
    }
}

/* ---------- tapa (abraza la caja por fuera) ---------- */
module tapa() {
    o = ajuste + falda_pared;        // lo que sobresale la tapa por cada lado
    px = ext_x + 2 * o;              // plato de la tapa
    py = ext_y + 2 * o;
    difference() {
        union() {
            // plato superior
            translate([-o, -o, 0]) bloque(px, py, tapa_grosor, radio + o, chaflan, abajo = false);
            // falda exterior que abraza las paredes de la caja
            translate([-o, -o, -falda_alto])
                difference() {
                    rect_redondo(px, py, falda_alto, radio + o);
                    translate([falda_pared, falda_pared, -1])
                        rect_redondo(px - 2 * falda_pared, py - 2 * falda_pared, falda_alto + 2, radio + ajuste);
                }
        }
        // orificio del SMA
        translate([ant_x, ant_y, -falda_alto - 1]) cylinder(d = ant_d, h = falda_alto + tapa_grosor + 2);
    }
}

/* ---------- conjunto aproximado (solo para la vista "montaje") ---------- */
module conjunto() {
    color("seagreen", 0.5) translate([pared + holgura, pared + holgura, suelo]) cube([conj_x, conj_y, conj_z]);
    color("dimgray") translate([ant_x, ant_y, caja_z]) cylinder(d = 6.35, h = tapa_grosor + 8);
    color("black") translate([ant_x, ant_y, caja_z + tapa_grosor + 8]) cylinder(d1 = 7, d2 = 5, h = ant_largo);
}

/* ---------- salida ---------- */
if (part == "caja") caja();
if (part == "tapa") translate([0, ext_y, tapa_grosor]) rotate([180, 0, 0]) tapa();   // boca abajo para imprimir
if (part == "ambas") {
    caja();
    translate([0, 2 * ext_y + 10, tapa_grosor]) rotate([180, 0, 0]) tapa();
}
if (part == "montaje") {
    caja();
    translate([0, 0, caja_z]) tapa();
    conjunto();
}
