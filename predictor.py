# -*- coding: utf-8 -*-
"""Línea de comandos del predictor del Mundial FIFA 2026.

Uso:
    python predictor.py                     # predicción completa
    python predictor.py --semilla 7         # otro sorteo de dieciseisavos/penaltis
    python predictor.py --sims 20000        # más simulaciones Monte Carlo
    python predictor.py --guardar mi.txt    # además, guarda la salida en un fichero
"""

import argparse
import sys
from collections import Counter

from datos import EQUIPOS
from torneo import ETIQUETAS, ORDEN_GRUPOS, RONDAS, jugar_torneo, montecarlo

ANCHO = 70
NOMBRE_RONDA = {
    "dieciseisavos": "DIECISEISAVOS DE FINAL",
    "octavos": "OCTAVOS DE FINAL",
    "cuartos": "CUARTOS DE FINAL",
    "semifinales": "SEMIFINALES",
    "final": "FINAL",
}


def _titulo(lineas, texto):
    lineas.append("")
    lineas.append("=" * ANCHO)
    lineas.append(texto)
    lineas.append("=" * ANCHO)


def _linea_partido(p, ganador=None, etiqueta="", verbo="pasa"):
    marcador = "%d-%d" % (p.goles_local, p.goles_visitante)
    if p.penales:
        marcador += " (pen)"
    texto = "  %-5s%20s  %-9s %-21s" % (etiqueta, p.local, marcador, p.visitante)
    if ganador:
        texto += " -> %s %s" % (verbo, ganador)
    return texto.rstrip()


def _seccion_grupos(lineas, res):
    _titulo(lineas, "FASE DE GRUPOS  (marcador exacto y clasificación)")
    for grupo in ORDEN_GRUPOS:
        lineas.append("")
        lineas.append("Grupo %s" % grupo)
        for p in res["partidos_grupos"][grupo]:
            lineas.append(_linea_partido(p))
        for pos, (nombre, s) in enumerate(res["tablas"][grupo], 1):
            lineas.append(
                "    %d. %-21s %2d pts  %2d-%-2d  dif %+d"
                % (pos, nombre, s["pts"], s["gf"], s["gc"], s["gf"] - s["gc"])
            )


def _seccion_terceros(lineas, res):
    _titulo(lineas, "RANKING DE TERCEROS  (los 8 primeros se clasifican)")
    for pos, (nombre, s) in enumerate(res["terceros"], 1):
        marca = "CLASIFICADO" if pos <= 8 else "eliminado"
        lineas.append(
            "  %2d. %-21s %2d pts  %2d-%-2d  dif %+d   %s"
            % (pos, nombre, s["pts"], s["gf"], s["gc"], s["gf"] - s["gc"], marca)
        )
    lineas.append("")
    lineas.append("  Nota: los segundos de I-L entran en el bombo de dieciseisavos junto")
    lineas.append("  a los 8 terceros (sorteo según la semilla; formato en el README).")


def _seccion_eliminatorias(lineas, res):
    for ronda in RONDAS:
        _titulo(lineas, NOMBRE_RONDA[ronda])
        verbo = "gana" if ronda == "final" else "pasa"
        for etiqueta, (p, ganador) in zip(ETIQUETAS[ronda], res["rondas"][ronda]):
            lineas.append(_linea_partido(p, ganador, etiqueta, verbo))
        if ronda == "semifinales":
            _titulo(lineas, "TERCER PUESTO")
            p, ganador = res["rondas"]["tercer_puesto"][0]
            lineas.append(_linea_partido(p, ganador, verbo="gana"))
    lineas.append("")
    lineas.append("  *** CAMPEÓN DEL MUNDO 2026: %s ***" % res["campeon"].upper())
    lineas.append("      Subcampeón: %s   |   Tercer puesto: %s"
                  % (res["subcampeon"], res["tercero"]))


def _seccion_resumen_porra(lineas, res):
    _titulo(lineas, "RESUMEN PARA RELLENAR LA PORRA (equipos por ronda)")
    for ronda in RONDAS:
        equipos = []
        for p, _ in res["rondas"][ronda]:
            equipos += [p.local, p.visitante]
        lineas.append("")
        lineas.append("  %s (%d):" % (NOMBRE_RONDA[ronda].capitalize(), len(equipos)))
        for i in range(0, len(equipos), 4):
            lineas.append("    " + ", ".join(equipos[i:i + 4]))
    lineas.append("")
    lineas.append("  Ganador de la final: %s" % res["campeon"])


def _goles_prediccion(res):
    """Goles a favor/en contra de cada equipo en la predicción determinista."""
    favor, contra = Counter(), Counter()
    todos = [p for grupo in res["partidos_grupos"].values() for p in grupo]
    todos += [p for ronda in res["rondas"].values() for p, _ in ronda]
    for p in todos:
        favor[p.local] += p.goles_local
        contra[p.local] += p.goles_visitante
        favor[p.visitante] += p.goles_visitante
        contra[p.visitante] += p.goles_local
    return favor, contra


def _seccion_premios(lineas, res):
    _titulo(lineas, "PREMIOS INDIVIDUALES (sugerencias)")
    favor, contra = _goles_prediccion(res)
    semifinalistas = [n for p, _ in res["rondas"]["semifinales"] for n in (p.local, p.visitante)]
    finalistas = [res["campeon"], res["subcampeon"]]

    eq_bota = max(semifinalistas, key=lambda n: favor[n])
    bota = EQUIPOS[eq_bota].estrella or ("delantero de %s" % eq_bota)
    mvp = EQUIPOS[res["campeon"]].estrella or ("figura de %s" % res["campeon"])
    eq_guante = min(finalistas, key=lambda n: contra[n])
    guante = EQUIPOS[eq_guante].portero or ("portero de %s" % eq_guante)

    lineas.append("  Bota de Oro : %s (%s, %d goles previstos del equipo)"
                  % (bota, eq_bota, favor[eq_bota]))
    lineas.append("  MVP         : %s (%s, campeón previsto)" % (mvp, res["campeon"]))
    lineas.append("  Guante de Oro: %s (%s, %d goles encajados previstos)"
                  % (guante, eq_guante, contra[eq_guante]))


def _seccion_categorias(lineas, mc):
    _titulo(lineas, "CATEGORÍAS DE GOLES DE LA PORRA  (media en %d simulaciones)" % mc["n"])
    n = float(mc["n"])
    favor = {e: mc["goles_favor"][e] / n for e in EQUIPOS}
    contra = {e: mc["goles_contra"][e] / n for e in EQUIPOS}

    lineas.append("")
    lineas.append("  Selección goleadora (+1 por gol a favor):")
    for e in sorted(EQUIPOS, key=lambda x: -favor[x])[:5]:
        lineas.append("    %-21s %5.1f goles esperados" % (e, favor[e]))

    lineas.append("")
    lineas.append("  Más goleada (+1 por gol en contra):")
    for e in sorted(EQUIPOS, key=lambda x: -contra[x])[:5]:
        lineas.append("    %-21s %5.1f goles en contra esperados" % (e, contra[e]))

    lineas.append("")
    lineas.append("  La más férrea (-2 por gol en contra, elegir la que menos encaje):")
    for e in sorted(EQUIPOS, key=lambda x: contra[x])[:5]:
        lineas.append("    %-21s %5.1f goles en contra esperados (%.1f pts)"
                      % (e, contra[e], -2 * contra[e]))

    recomendado_gol = max(EQUIPOS, key=lambda x: favor[x])
    recomendado_goleada = max(EQUIPOS, key=lambda x: contra[x])
    recomendado_ferrea = min(EQUIPOS, key=lambda x: contra[x])
    lineas.append("")
    lineas.append("  Recomendación: goleadora %s | más goleada %s | férrea %s"
                  % (recomendado_gol, recomendado_goleada, recomendado_ferrea))


def _seccion_probabilidades(lineas, mc):
    _titulo(lineas, "PROBABILIDADES MONTE CARLO  (%d torneos simulados)" % mc["n"])
    n = float(mc["n"])
    lineas.append("")
    lineas.append("  %-21s %8s %8s %8s %8s" % ("", "Campeón", "Final", "Semis", "Cuartos"))
    top = sorted(EQUIPOS, key=lambda e: -mc["campeonatos"][e])[:12]
    for e in top:
        lineas.append("  %-21s %7.1f%% %7.1f%% %7.1f%% %7.1f%%" % (
            e,
            100 * mc["campeonatos"][e] / n,
            100 * mc["apariciones"]["final"][e] / n,
            100 * mc["apariciones"]["semifinales"][e] / n,
            100 * mc["apariciones"]["cuartos"][e] / n,
        ))


def main():
    try:
        # con la salida redirigida a fichero/tubería, mejor UTF-8 que cp1252
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    parser = argparse.ArgumentParser(description="Predictor del Mundial 2026 para la porra")
    parser.add_argument("--semilla", type=int, default=2026,
                        help="semilla del sorteo de dieciseisavos (defecto: 2026)")
    parser.add_argument("--sims", type=int, default=5000,
                        help="simulaciones Monte Carlo (0 para desactivar; defecto: 5000)")
    parser.add_argument("--guardar", metavar="FICHERO",
                        help="guardar la salida también en un fichero de texto")
    args = parser.parse_args()

    res = jugar_torneo(semilla=args.semilla)

    lineas = []
    lineas.append("=" * ANCHO)
    lineas.append("PREDICTOR MUNDIAL FIFA 2026   (semilla %d)" % args.semilla)
    lineas.append("=" * ANCHO)

    _seccion_grupos(lineas, res)
    _seccion_terceros(lineas, res)
    _seccion_eliminatorias(lineas, res)
    _seccion_resumen_porra(lineas, res)
    _seccion_premios(lineas, res)

    if args.sims > 0:
        mc = montecarlo(args.sims, semilla=args.semilla)
        _seccion_categorias(lineas, mc)
        _seccion_probabilidades(lineas, mc)

    salida = "\n".join(lineas)
    print(salida)
    if args.guardar:
        with open(args.guardar, "w", encoding="utf-8") as fichero:
            fichero.write(salida + "\n")
        print("\nGuardado en %s" % args.guardar)


if __name__ == "__main__":
    main()
