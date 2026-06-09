# -*- coding: utf-8 -*-
"""Simulación del torneo completo: fase de grupos, ranking de terceros,
sorteo de dieciseisavos, eliminatorias y Monte Carlo. El formato del cuadro
está descrito en el README.
"""

import itertools
import random
from collections import Counter, namedtuple

from datos import EQUIPOS, GRUPOS, valoracion
from modelo import (
    goles_esperados,
    marcador_mas_probable,
    muestrear_marcador,
    prediccion_marcador,
    probabilidades_1x2,
)

Partido = namedtuple("Partido", "local visitante goles_local goles_visitante penales")

ORDEN_GRUPOS = "ABCDEFGHIJKL"
RONDAS = ["dieciseisavos", "octavos", "cuartos", "semifinales", "final"]
ETIQUETAS = {
    "dieciseisavos": ["P%02d" % i for i in range(1, 17)],
    "octavos": ["O%d" % i for i in range(1, 9)],
    "cuartos": ["C%d" % i for i in range(1, 5)],
    "semifinales": ["S1", "S2"],
    "final": ["F"],
}


def _partido_grupos(a, b, rng):
    """rng=None -> marcador más probable (predicción); con rng -> muestreo."""
    lam_a, lam_b = goles_esperados(a, b), goles_esperados(b, a)
    if rng is None:
        ga, gb = prediccion_marcador(lam_a, lam_b)
    else:
        ga, gb = muestrear_marcador(lam_a, lam_b, rng)
    return Partido(a, b, ga, gb, False)


def _clasificar(nombres, partidos):
    stats = {n: {"pts": 0, "gf": 0, "gc": 0} for n in nombres}
    for p in partidos:
        local, visit = stats[p.local], stats[p.visitante]
        local["gf"] += p.goles_local
        local["gc"] += p.goles_visitante
        visit["gf"] += p.goles_visitante
        visit["gc"] += p.goles_local
        if p.goles_local > p.goles_visitante:
            local["pts"] += 3
        elif p.goles_local < p.goles_visitante:
            visit["pts"] += 3
        else:
            local["pts"] += 1
            visit["pts"] += 1
    orden = sorted(
        nombres,
        key=lambda n: (
            -stats[n]["pts"],
            -(stats[n]["gf"] - stats[n]["gc"]),
            -stats[n]["gf"],
            -valoracion(n),
            n,
        ),
    )
    return [(n, stats[n]) for n in orden]


def jugar_fase_grupos(rng=None):
    partidos, tablas = {}, {}
    for grupo, nombres in GRUPOS.items():
        jugados = [_partido_grupos(a, b, rng) for a, b in itertools.combinations(nombres, 2)]
        partidos[grupo] = jugados
        tablas[grupo] = _clasificar(nombres, jugados)
    return partidos, tablas


def ranking_terceros(tablas):
    """Los 12 terceros ordenados; los 8 primeros se clasifican."""
    terceros = [tablas[g][2] for g in ORDEN_GRUPOS]
    return sorted(
        terceros,
        key=lambda par: (
            -par[1]["pts"],
            -(par[1]["gf"] - par[1]["gc"]),
            -par[1]["gf"],
            -valoracion(par[0]),
            par[0],
        ),
    )


def _sorteo_dieciseisavos(tablas, terceros_clasificados, rng):
    """Asigna el bombo (8 terceros + segundos de I-L) a los 12 primeros."""
    primeros = [tablas[g][0][0] for g in ORDEN_GRUPOS]
    bombo = [n for n, _ in terceros_clasificados] + [tablas[g][1][0] for g in "IJKL"]
    for _ in range(10000):
        rng.shuffle(bombo)
        if all(EQUIPOS[rival].grupo != EQUIPOS[cabeza].grupo
               for cabeza, rival in zip(primeros, bombo)):
            break
    cruces = list(zip(primeros, bombo))
    # P13-P16: los segundos de A-H se cruzan entre sí
    cruces += [
        (tablas["A"][1][0], tablas["B"][1][0]),
        (tablas["C"][1][0], tablas["D"][1][0]),
        (tablas["E"][1][0], tablas["F"][1][0]),
        (tablas["G"][1][0], tablas["H"][1][0]),
    ]
    return cruces


def _partido_eliminatoria(a, b, rng):
    lam_a = goles_esperados(a, b, True)
    lam_b = goles_esperados(b, a, True)
    exp_a, exp_b = EQUIPOS[a].experiencia, EQUIPOS[b].experiencia
    p_penales_a = (exp_a + 1.0) / (exp_a + exp_b + 2.0)
    if rng is None:
        p1, px, p2 = probabilidades_1x2(lam_a, lam_b)
        gana_a = p1 + px * p_penales_a >= p2 + px * (1.0 - p_penales_a)
        if px >= p1 and px >= p2:
            ga, gb = marcador_mas_probable(lam_a, lam_b, "empate")
            penales = True
        else:
            # marcador coherente con el clasificado elegido
            ga, gb = marcador_mas_probable(lam_a, lam_b, "local" if gana_a else "visitante")
            penales = False
    else:
        ga, gb = muestrear_marcador(lam_a, lam_b, rng)
        penales = ga == gb
        gana_a = ga > gb or (penales and rng.random() < p_penales_a)
    ganador = a if gana_a else b
    return Partido(a, b, ga, gb, penales), ganador


def jugar_torneo(semilla=2026, rng_partidos=None):
    """Torneo completo.

    rng_partidos=None -> predicción determinista (marcadores más probables).
    Con un random.Random -> simulación aleatoria (para el Monte Carlo).
    La semilla controla el sorteo del bombo de dieciseisavos.
    """
    rng_sorteo = rng_partidos if rng_partidos is not None else random.Random(semilla)
    partidos_grupos, tablas = jugar_fase_grupos(rng_partidos)
    terceros = ranking_terceros(tablas)
    cruces = _sorteo_dieciseisavos(tablas, terceros[:8], rng_sorteo)

    rondas = {}
    ganadores = []
    perdedores_semis = []
    for ronda in RONDAS:
        if ronda != "dieciseisavos":
            cruces = list(zip(ganadores[0::2], ganadores[1::2]))
        resultados, ganadores = [], []
        for a, b in cruces:
            partido, ganador = _partido_eliminatoria(a, b, rng_partidos)
            resultados.append((partido, ganador))
            ganadores.append(ganador)
            if ronda == "semifinales":
                perdedores_semis.append(a if ganador == b else b)
        rondas[ronda] = resultados

    tercer_puesto, tercero = _partido_eliminatoria(
        perdedores_semis[0], perdedores_semis[1], rng_partidos
    )
    rondas["tercer_puesto"] = [(tercer_puesto, tercero)]

    partido_final, campeon = rondas["final"][0]
    subcampeon = partido_final.visitante if campeon == partido_final.local else partido_final.local

    return {
        "partidos_grupos": partidos_grupos,
        "tablas": tablas,
        "terceros": terceros,
        "rondas": rondas,
        "campeon": campeon,
        "subcampeon": subcampeon,
        "tercero": tercero,
    }


def montecarlo(n_simulaciones, semilla=2026):
    """Repite el torneo con resultados aleatorios y acumula estadísticas."""
    rng = random.Random(semilla * 7919 + 1)
    goles_favor = Counter()
    goles_contra = Counter()
    apariciones = {ronda: Counter() for ronda in RONDAS}
    campeonatos = Counter()

    for _ in range(n_simulaciones):
        res = jugar_torneo(rng_partidos=rng)
        todos = [p for grupo in res["partidos_grupos"].values() for p in grupo]
        todos += [p for ronda in res["rondas"].values() for p, _ in ronda]
        for p in todos:
            goles_favor[p.local] += p.goles_local
            goles_contra[p.local] += p.goles_visitante
            goles_favor[p.visitante] += p.goles_visitante
            goles_contra[p.visitante] += p.goles_local
        for ronda in RONDAS:
            for p, _ in res["rondas"][ronda]:
                apariciones[ronda][p.local] += 1
                apariciones[ronda][p.visitante] += 1
        campeonatos[res["campeon"]] += 1

    return {
        "n": n_simulaciones,
        "goles_favor": goles_favor,
        "goles_contra": goles_contra,
        "apariciones": apariciones,
        "campeonatos": campeonatos,
    }
