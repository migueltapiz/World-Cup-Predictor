# -*- coding: utf-8 -*-
"""Modelo de "choque" entre selecciones.

Convierte las valoraciones de dos equipos en goles esperados (lambda) y, a
partir de una matriz conjunta Poisson + Dixon-Coles, calcula probabilidades
1X2, marcadores más probables y muestras para el Monte Carlo. La fórmula
del choque y la calibración de los parámetros están en el README.
"""

import math
from bisect import bisect
from functools import lru_cache

from datos import AJUSTES_GRUPOS, EQUIPOS

BASE_GOLES = 1.32        # goles esperados contra un rival idéntico
K_CHOQUE = 2.4           # sensibilidad a la diferencia de valoraciones
RHO_DIXON_COLES = -0.06  # corrección de dependencia en marcadores bajos
MAX_GOLES = 8            # tope de la distribución de goles por equipo


def _fuerza_ofensiva(eq):
    return eq.ataque * 0.7 + eq.medio * 0.3


def _fuerza_defensiva(eq):
    return eq.defensa * 0.7 + eq.medio * 0.3


@lru_cache(maxsize=None)
def goles_esperados(nombre, rival, eliminatoria=False):
    """Goles esperados de `nombre` contra `rival` (el choque de factores)."""
    eq, rv = EQUIPOS[nombre], EQUIPOS[rival]
    diferencia = (_fuerza_ofensiva(eq) - _fuerza_defensiva(rv)) / 100.0
    lam = BASE_GOLES * math.exp(K_CHOQUE * diferencia)
    lam *= 1.0 + 0.02 * (eq.forma - 5.5)
    if eliminatoria:
        # el pedigrí pesa más cuando no hay margen de error
        lam *= 1.0 + 0.015 * (eq.experiencia - 5.5)
    else:
        lam *= AJUSTES_GRUPOS.get((nombre, rival), 1.0)
    lam *= eq.bonus_local
    lam *= rv.factor_portero
    return lam


@lru_cache(maxsize=None)
def _poisson(lam):
    return tuple(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(MAX_GOLES + 1))


def _tau_dixon_coles(i, j, lam_a, lam_b):
    rho = RHO_DIXON_COLES
    if i == 0 and j == 0:
        return 1.0 - lam_a * lam_b * rho
    if i == 0 and j == 1:
        return 1.0 + lam_a * rho
    if i == 1 and j == 0:
        return 1.0 + lam_b * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


@lru_cache(maxsize=None)
def matriz_marcadores(lam_a, lam_b):
    """P(marcador i-j) para i, j en 0..MAX_GOLES, con Dixon-Coles, normalizada."""
    dist_a, dist_b = _poisson(lam_a), _poisson(lam_b)
    matriz = [
        [dist_a[i] * dist_b[j] * _tau_dixon_coles(i, j, lam_a, lam_b)
         for j in range(MAX_GOLES + 1)]
        for i in range(MAX_GOLES + 1)
    ]
    total = sum(sum(fila) for fila in matriz)
    return tuple(tuple(p / total for p in fila) for fila in matriz)


@lru_cache(maxsize=None)
def _acumulada(lam_a, lam_b):
    plana, suma = [], 0.0
    for fila in matriz_marcadores(lam_a, lam_b):
        for p in fila:
            suma += p
            plana.append(suma)
    return tuple(plana)


def muestrear_marcador(lam_a, lam_b, rng):
    """Un marcador (ga, gb) muestreado de la matriz (para el Monte Carlo)."""
    indice = bisect(_acumulada(lam_a, lam_b), rng.random())
    indice = min(indice, (MAX_GOLES + 1) ** 2 - 1)
    return divmod(indice, MAX_GOLES + 1)


def marcador_mas_probable(lam_a, lam_b, condicion=None):
    """Marcador (ga, gb) más probable.

    condicion: None (cualquiera), "local" (gana A), "empate" o "visitante" (gana B).
    """
    matriz = matriz_marcadores(lam_a, lam_b)
    mejor, mejor_p = (0, 0), -1.0
    for i, fila in enumerate(matriz):
        for j, p in enumerate(fila):
            if condicion == "local" and i <= j:
                continue
            if condicion == "empate" and i != j:
                continue
            if condicion == "visitante" and j <= i:
                continue
            if p > mejor_p:
                mejor, mejor_p = (i, j), p
    return mejor


def prediccion_marcador(lam_a, lam_b):
    """Marcador para la porra: primero el signo 1X2 más probable (2 puntos),
    después el marcador más probable dentro de ese signo (1 punto extra)."""
    p1, px, p2 = probabilidades_1x2(lam_a, lam_b)
    if px >= p1 and px >= p2:
        condicion = "empate"
    elif p1 >= p2:
        condicion = "local"
    else:
        condicion = "visitante"
    return marcador_mas_probable(lam_a, lam_b, condicion)


def probabilidades_1x2(lam_a, lam_b):
    """(P gana A, P empate, P gana B) según la matriz de marcadores."""
    matriz = matriz_marcadores(lam_a, lam_b)
    p1 = px = p2 = 0.0
    for i, fila in enumerate(matriz):
        for j, p in enumerate(fila):
            if i > j:
                p1 += p
            elif i == j:
                px += p
            else:
                p2 += p
    return p1, px, p2
