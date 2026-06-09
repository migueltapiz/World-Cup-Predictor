# World-Cup-Predictor

Predictor de resultados del Mundial FIFA 2026 escrito en Python puro, sin
dependencias externas. Genera una predicción completa del torneo —
marcadores exactos de la fase de grupos, clasificaciones, ranking de
terceros y cuadro eliminatorio hasta el campeón — y la acompaña de un
análisis Monte Carlo con las probabilidades de cada selección. Está pensado
para rellenar una porra, pero sirve igual como pequeño experimento de
modelado de fútbol.

## Requisitos

- Python 3.8 o superior. Nada más: solo biblioteca estándar.

## Cómo lanzarlo

```bash
git clone https://github.com/<usuario>/World-Cup-Predictor.git
cd World-Cup-Predictor
python predictor.py
```

Opciones de la línea de comandos:

| Opción | Descripción | Por defecto |
|---|---|---|
| `--semilla N` | Semilla del sorteo de dieciseisavos y de los desempates a penaltis. Con la misma semilla la predicción es siempre idéntica. | `2026` |
| `--sims N` | Número de torneos simulados en el Monte Carlo (`0` lo desactiva). | `5000` |
| `--guardar FICHERO` | Además de imprimirla, guarda la salida en un fichero de texto (UTF-8). | — |

La ejecución completa tarda unos 3 segundos e imprime, por secciones:

1. **Fase de grupos**: marcador exacto de los 72 partidos y tabla de cada grupo.
2. **Ranking de terceros**: los 12 terceros ordenados; los 8 primeros se clasifican.
3. **Eliminatorias**: dieciseisavos, octavos, cuartos, semifinales, tercer
   puesto y final, con marcador y clasificado de cada cruce.
4. **Resumen para la porra**: la lista de equipos que alcanza cada ronda.
5. **Premios individuales**: sugerencias de Bota de Oro, MVP y Guante de Oro
   a partir de las figuras de los equipos que llegan lejos.
6. **Categorías de goles** (Monte Carlo): goles esperados a favor y en
   contra de cada selección, para apuestas de tipo "equipo más goleador" o
   "equipo que menos encaja".
7. **Probabilidades** (Monte Carlo): opciones de cada selección de ser
   campeona o de alcanzar la final, semifinales y cuartos.

## El modelo

### Valoraciones por factores

Cada selección se describe en [datos.py](datos.py) con estos factores:

| Factor | Qué representa |
|---|---|
| `ataque`, `medio`, `defensa` | Calidad de cada línea (0-100). La escala está anclada al Elo real: `overall ≈ 40 + (Elo − 1300) × 0.062`, con el top-12 fijado al Elo de eloratings.net de junio de 2026. |
| `forma` | Momento actual de la selección (0-10). |
| `experiencia` | Pedigrí en grandes torneos (0-10); solo pesa en eliminatorias. |
| `bonus_local` | Multiplicador de anfitrión: México ×1.30 (incluye la altitud del Azteca), EEUU ×1.22, Canadá ×1.15. |
| `factor_portero` | Recorte a los goles esperados del rival: portero de élite ×0.92, bueno ×0.96, resto ×1.00. |
| `estrella`, `portero` | Figuras usadas para las sugerencias de premios individuales. |

### El "choque" entre dos selecciones

Al enfrentarse A contra B, los goles esperados de A salen de enfrentar su
fuerza ofensiva con la fuerza defensiva de B ([modelo.py](modelo.py)):

```
OF_A = 0.7 · ataque_A + 0.3 · medio_A
DEF_B = 0.7 · defensa_B + 0.3 · medio_B

λ_A = BASE_GOLES · exp(K_CHOQUE · (OF_A − DEF_B) / 100)
      · forma · experiencia(solo eliminatorias) · bonus_local_A · factor_portero_B
```

con `BASE_GOLES = 1.32` (~2.6 goles por partido entre rivales idénticos) y
`K_CHOQUE = 2.4` (~+0.45 goles por cada 100 puntos Elo de ventaja).

### Distribución de marcadores

Los dos λ alimentan una Poisson truncada (0-8 goles por equipo) corregida
con **Dixon-Coles** (`ρ = −0.06`), que sube la probabilidad de los empates
de marcador bajo (0-0, 1-1) que la Poisson independiente infravalora. De esa
matriz conjunta de marcadores salen las probabilidades 1X2, el marcador más
probable y las muestras aleatorias del Monte Carlo.

### Predicción determinista vs. Monte Carlo

- **La predicción "oficial"** es determinista: en cada partido se elige
  primero el signo 1X2 más probable y, dentro de ese signo, el marcador más
  probable (en una porra típica el signo vale más que el resultado exacto,
  así que se prioriza). En eliminatorias, si el marcador más probable es un
  empate, el clasificado se decide por la probabilidad de victoria más un
  desempate a penaltis ponderado por la experiencia.
- **El Monte Carlo** repite el torneo entero miles de veces muestreando
  marcadores de la matriz, y de ahí salen las probabilidades por ronda y
  las medias de goles a favor y en contra de cada selección.

## Calibración

Métricas del modelo simulando la fase de grupos (3.000 réplicas):

| Métrica | Valor simulado | Referencia |
|---|---|---|
| Goles por partido | ~3.0 | 2.6-2.7 en Mundiales recientes; el formato de 48 con más desajustes la eleva |
| Empates en grupos | ~21% | Rango histórico ~17-25% |
| Goleadas (diferencia ≥ 3) | ~23% | Frecuentes entre cabezas de serie y debutantes |

Las probabilidades de campeón resultantes (España ~22%, Argentina ~15%,
Francia ~10%, anfitriones como outsiders) siguen el mismo orden que el Elo,
los mercados de predicción y el supercomputer de Opta de junio de 2026.

Umbrales orientativos si retocas valoraciones y quieres re-calibrar:

- Media de goles < 2.5/partido → sube `BASE_GOLES` hacia 1.35.
- Goleadas demasiado raras → sube `K_CHOQUE` hacia 2.6.
- Empates en grupos < ~15% → haz `RHO_DIXON_COLES` más negativo (−0.08 a −0.10).

## Formato del torneo

48 selecciones en 12 grupos de 4. Se clasifican el 1.º y el 2.º de cada
grupo más los 8 mejores terceros (32 equipos). En dieciseisavos, los 12
primeros de grupo se enfrentan a un bombo formado por los 8 mejores
terceros y los segundos de los grupos I-L (sorteo dependiente de la
semilla, evitando cruces entre equipos del mismo grupo), mientras que los
segundos de los grupos A-H se cruzan entre sí. De ahí en adelante el cuadro
es fijo hasta la final, con partido por el tercer puesto.

## Personalización

- **Valoraciones**: edita los números de [datos.py](datos.py) y vuelve a
  ejecutar; todo lo demás se recalcula solo.
- **Ajustes por partido**: `AJUSTES_GRUPOS` en [datos.py](datos.py) aplica
  multiplicadores a partidos concretos de la fase de grupos (por ejemplo,
  una baja por lesión en los primeros encuentros).
- **Parámetros del modelo**: `BASE_GOLES`, `K_CHOQUE` y `RHO_DIXON_COLES`
  viven al principio de [modelo.py](modelo.py).
- **Otro cuadro**: cambia `--semilla` para explorar otros sorteos de
  dieciseisavos sin tocar el código.

## Estructura del proyecto

| Fichero | Contenido |
|---|---|
| [datos.py](datos.py) | Grupos, valoraciones y figuras de cada selección |
| [modelo.py](modelo.py) | Choque de factores, Poisson + Dixon-Coles, marcadores y probabilidades |
| [torneo.py](torneo.py) | Fase de grupos, terceros, sorteo, eliminatorias y Monte Carlo |
| [predictor.py](predictor.py) | Línea de comandos y salida formateada |
