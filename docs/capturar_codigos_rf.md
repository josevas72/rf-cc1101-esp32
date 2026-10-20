# Guía rápida: capturar códigos RF de un mando y convertirlos en entidades

Objetivo: capturar lo que emite un mando de 433 MHz y dárselo a Claude para que deduzca el
protocolo y genere el YAML (luz, interruptor, persiana, ventilador, botón…).

---

## 1. Activar el modo captura

En tu YAML (`rf-cc1101-c3-supermini.yaml` o `rf-cc1101-xiao-c6.yaml`), descomenta el `dump` del `remote_receiver` **solo mientras capturas**:

```yaml
remote_receiver:
  - id: receiver0
    pin:
      number: ${pin_gdo0}
      mode: {input: true, output: true, pullup: true, open_drain: true}
      allow_other_uses: true
    dump:
      - rc_switch      # intenta decodificar (protocolo + código en binario)
      - raw            # pulsos en bruto, sirve si rc_switch no decodifica
    tolerance: 50%
    filter: 150us
    idle: 4ms
```

Notas:
- `dump: raw` genera mucho log y carga el ESP: **comenta el `raw` al terminar**.
- El CC1101 tiene que estar escuchando (`cc1101.begin_rx` en `on_boot`, ya incluido).
- Abre los logs desde el panel de ESPHome o desde el `web_server` (`http://IP`).

## 2. Capturar

1. Acércate al módulo (10-30 cm) con el mando, antena puesta.
2. Pulsa **un botón cada vez**, corto, y apunta cuál es. Repite **3 veces** cada botón.
3. Prueba también pulsación **larga** si el mando la usa (por ejemplo regular intensidad).
4. Copia el log completo de cada botón, sin recortar. Líneas típicas:

```
Received RCSwitch Raw: protocol=6 data='001011111010110001010011'
Received Raw: 345, -1020, 690, -690, ...
```

Qué significa:
- **Sale `RCSwitch Raw` con protocolo y datos:** está decodificado. Es lo ideal.
- **Solo sale `Received Raw`:** el protocolo no es de los conocidos; Claude lo analizará a mano.
- **No sale nada:** revisa que el mando es de 433 MHz (el E07-M1101D cubre 387-464 MHz; si es de
  868 MHz o 315 MHz no lo oirá), acércalo más y prueba `filter: 100us` o una frecuencia
  ligeramente distinta (433.42MHz o 434.0MHz) en `cc1101:`.

## 3. Qué entregarle a Claude

Pega este texto rellenando lo que falta:

```
Tengo un mando RF de 433 MHz de: [ventilador / persiana / luz / enchufe ...] (marca/modelo: ...).
Quiero que me des un YAML de ESPHome con las entidades correctas y los binary_sensor para
sincronizar el estado cuando use el mando original.

Botones del mando (en orden): [1: luz, 2: velocidad 1, 3: velocidad 2, 4: parar, ...]

Logs de cada botón (3 pulsaciones cada uno):
BOTÓN 1 (luz): <pegar log rc_switch y raw>
BOTÓN 2 (...): <pegar log>
...

Mi YAML base: el adjunto (rf-cc1101-*.yaml): CC1101 con GDO0 en un único pin, transmitter0 y receiver0.

Entidades que busco: [light / switch / cover / fan / button ...]
Datos extra: [duración de la persiana en abrir y cerrar, número de velocidades del ventilador,
si la luz es "toggle" (un botón alterna) o tiene encendido y apagado separados ...]
```

Adjunta también tu YAML (quitando la clave de la API y la contraseña del punto de acceso).

## 4. Qué debe devolverte Claude

- Protocolo, longitud de pulso y códigos de cada botón.
- Bloque `remote_transmitter.transmit_rc_switch_raw` (o `transmit_raw`) por cada acción, con
  repeticiones.
- Entidades según el dispositivo: `cover` para persianas, `light`/`switch` para luces y enchufes,
  ventilador con sus velocidades, y `button` para acciones sueltas.
- `binary_sensor` con `remote_receiver` que escuchan el mando original y actualizan el estado.
- Un **botón de prueba** por código para comprobar la emisión antes de montar todo.

## 5. Probar la emisión

Antes de crear entidades definitivas, un botón de prueba por código:

```yaml
button:
  - platform: template
    name: "TEST RF - botón 1"
    on_press:
      - remote_transmitter.transmit_rc_switch_raw:
          code: "001011111010110001010011"   # el código capturado
          protocol: 6                        # el protocolo que mostró el log
          repeat: { times: 10, wait_time: 0s }
```

Si no responde el aparato, sube `times` (de 10 a 15-20) o dile a Claude qué ve en el log.

## 6. Cuándo no funciona la copia

- **Código variable (rolling code):** si cada pulsación del mismo botón da un código distinto
  (con otros bits cambiando), el mando es de código dinámico y no se puede copiar con un código
  fijo. Compara las 3 pulsaciones: deben salir iguales.
- **Botones "toggle":** un mismo código alterna encendido y apagado. El estado en HA será
  supuesto (no leído) y se descompensa si usas también el mando; Claude lo resolverá con el
  receptor.
- **Aparatos con dirección o ID:** dos mandos iguales pueden diferir en unos bits del código.
  Captura siempre con **tu** mando.

## 7. Al terminar

1. Comenta `- raw` (y `- rc_switch` si quieres) en el `dump` del receptor.
2. Guarda los códigos en un archivo, por ejemplo `codigos_rf.md`, con la tabla botón → protocolo →
   código.
3. Anota el aparato, la fecha y si funcionó la emisión.

---

## 8. Persianas: capturar abrir / cerrar / parar

Las persianas suelen usar 3 botones (subir, bajar, stop) con un código fijo de 24 bits. Pasos:

1. Activa `dump: rc_switch` y `raw`. Pulsa **subir** 3 veces, anota el log. Repite con **bajar** y **parar**.
2. Los tres códigos deben coincidir en casi todos los bits y diferir solo en los últimos
   (ejemplo: `...10100011` subir, `...10100001` bajar, `...10100010` parar). Eso es buena señal.
3. Apunta el **protocolo** (número, o los valores `pulse_length / sync / zero / one` si es
   personalizado) y los **tiempos** de subida y bajada completas (cronómetro).
4. Rellena los `xxxxx` del ejemplo `cover:` de tu YAML. Usa `time_based` con
   `open_duration` y `close_duration`.
5. Los códigos que **emite** tu mando pueden decodificarse con un protocolo distinto al que
   necesitas para **transmitir** (se ve a veces: se recibe con protocolo 6 y se emite con uno
   personalizado e invertido). Si al emitir no responde, prueba `inverted: true` o dale los logs
   `raw` a Claude para que ajuste el protocolo.
6. Para que Home Assistant sepa cuándo usas el mando original, añade los `binary_sensor` del
   ejemplo con los códigos **recibidos** y `delayed_off: 800ms`.

## 9. Capturar códigos RAW y adaptar el protocolo con Claude

Cuando `rc_switch` no decodifica (solo ves `Received Raw`) o decodifica pero el aparato no
responde al emitir, el camino es trabajar con los pulsos en bruto.

### 9.1 Captura

1. Activa **solo** `- raw` en el `dump`. Quita `rc_switch` para que el log sea limpio.
2. Pulsa el botón **una vez**, corto. Copia el bloque completo, p. ej.:

```
Received Raw: 345, -1020, 690, -690, 345, -1035, ...
```

3. Repite 3 veces por botón y copia **todas**; sirven para comparar y quitar ruido.
4. Si ves muchas líneas basura, acerca el mando, sube `filter` a `200us` o prueba
   `rx_attenuation: 6dB`.

### 9.2 Entregárselo a Claude

```
Adjunto capturas RAW de un mando RF de 433 MHz de [aparato]. 3 pulsaciones por botón.
Necesito: (1) identificar el protocolo (preámbulo/sync, duración del pulso, codificación de 0 y 1,
número de bits y repeticiones), (2) el protocolo personalizado para ESPHome
(transmit_rc_switch_raw con pulse_length/sync/zero/one/inverted, o transmit_raw si no encaja),
(3) el YAML de las entidades. Botón 1 = ... ; Botón 2 = ...
[pegar logs]
```

### 9.3 Probar un RAW desde Home Assistant

El YAML incluye la acción `rf_raw`. En *Herramientas de desarrollo → Acciones* busca
`esphome.<tu_dispositivo>_rf_raw` y manda:

```yaml
codigo: [345, -1020, 690, -690, 345, -1035]   # pulsos pegados del log
veces: 10
pausa: 10        # ms entre repeticiones
```

Positivo = señal, negativo = silencio, en microsegundos. Así pruebas lo que Claude te proponga
sin recompilar. Existen también `rf_rc_switch_protocolo_1` y `rf_rc_switch_protocolo_6`
para códigos binarios.

### 9.4 Si funciona

Pasa el resultado a `transmit_rc_switch_raw` o `transmit_raw` en el YAML y comenta el `dump`.
