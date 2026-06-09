# -*- coding: utf-8 -*-
"""Datos del Mundial 2026: grupos, valoraciones y figuras de cada selección.

El significado y la escala de cada factor están documentados en el README.
Plantillas y lesiones según la información disponible a 9 de junio de 2026.
"""

from collections import OrderedDict, namedtuple

Equipo = namedtuple(
    "Equipo",
    "nombre grupo ataque medio defensa forma experiencia bonus_local factor_portero estrella portero",
)

_DATOS = [
    # nombre, grupo, ataque, medio, defensa, forma, exp, b.local, f.portero, estrella, portero
    ("México", "A", 73, 74, 72, 6, 7, 1.30, 1.00, "Santiago Giménez", "Luis Malagón"),
    ("Sudáfrica", "A", 60, 60, 58, 5, 4, 1.0, 1.00, "", ""),
    ("República de Corea", "A", 67, 67, 64, 6, 6, 1.0, 1.00, "Son Heung-min", ""),
    ("Chequia", "A", 64, 65, 63, 5, 5, 1.0, 1.00, "Patrik Schick", ""),

    ("Canadá", "B", 67, 67, 66, 7, 4, 1.15, 1.00, "Jonathan David", ""),
    ("Bosnia y Herzegovina", "B", 65, 65, 63, 6, 4, 1.0, 1.00, "Edin Džeko", ""),
    ("Catar", "B", 57, 58, 55, 4, 3, 1.0, 1.00, "", ""),
    ("Suiza", "B", 71, 72, 72, 7, 7, 1.0, 0.96, "Breel Embolo", "Gregor Kobel"),

    ("Brasil", "C", 86, 84, 82, 6, 10, 1.0, 0.92, "Vinícius Júnior", "Alisson"),
    ("Marruecos", "C", 78, 79, 80, 7, 8, 1.0, 0.92, "Achraf Hakimi", "Yassine Bounou"),
    ("Haití", "C", 52, 52, 50, 4, 1, 1.0, 1.00, "", ""),
    ("Escocia", "C", 65, 68, 65, 7, 4, 1.0, 1.00, "Scott McTominay", ""),

    ("Estados Unidos", "D", 68, 68, 67, 6, 6, 1.22, 1.00, "Christian Pulisic", "Matt Turner"),
    ("Paraguay", "D", 64, 66, 69, 7, 4, 1.0, 1.00, "", ""),
    ("Australia", "D", 64, 65, 66, 6, 5, 1.0, 1.00, "", ""),
    ("Turquía", "D", 73, 72, 68, 8, 5, 1.0, 1.00, "Arda Güler", ""),

    ("Alemania", "E", 82, 82, 80, 7, 10, 1.0, 0.96, "Jamal Musiala", "Manuel Neuer"),
    ("Curaçao", "E", 50, 51, 50, 6, 1, 1.0, 1.00, "", ""),
    ("Costa de Marfil", "E", 70, 70, 68, 7, 5, 1.0, 1.00, "", ""),
    ("Ecuador", "E", 78, 79, 84, 7, 5, 1.0, 1.00, "Moisés Caicedo", ""),

    ("Países Bajos", "F", 83, 82, 80, 8, 8, 1.0, 0.96, "Cody Gakpo", "Bart Verbruggen"),
    ("Japón", "F", 76, 77, 74, 8, 6, 1.0, 1.00, "Takefusa Kubo", "Zion Suzuki"),
    ("Suecia", "F", 66, 62, 62, 4, 5, 1.0, 1.00, "Viktor Gyökeres", ""),
    ("Túnez", "F", 62, 64, 66, 6, 4, 1.0, 1.00, "", ""),

    ("Bélgica", "G", 78, 78, 74, 6, 7, 1.0, 0.92, "Kevin De Bruyne", "Thibaut Courtois"),
    ("Egipto", "G", 66, 63, 64, 7, 5, 1.0, 1.00, "Mohamed Salah", ""),
    ("Irán", "G", 62, 61, 62, 6, 5, 1.0, 1.00, "Mehdi Taremi", ""),
    ("Nueva Zelanda", "G", 53, 53, 54, 5, 2, 1.0, 1.00, "", ""),

    ("España", "H", 94, 95, 88, 10, 9, 1.0, 0.96, "Lamine Yamal", "Unai Simón"),
    ("Cabo Verde", "H", 55, 56, 55, 7, 1, 1.0, 1.00, "", ""),
    ("Arabia Saudí", "H", 57, 58, 55, 5, 4, 1.0, 1.00, "", ""),
    ("Uruguay", "H", 78, 77, 80, 7, 8, 1.0, 0.96, "Darwin Núñez", "Sergio Rochet"),

    ("Francia", "I", 90, 86, 85, 8, 10, 1.0, 0.92, "Kylian Mbappé", "Mike Maignan"),
    ("Senegal", "I", 75, 75, 75, 8, 6, 1.0, 0.96, "Sadio Mané", "Édouard Mendy"),
    ("Irak", "I", 53, 54, 53, 5, 2, 1.0, 1.00, "", ""),
    ("Noruega", "I", 85, 77, 75, 9, 3, 1.0, 1.00, "Erling Haaland", ""),

    ("Argentina", "J", 91, 90, 87, 9, 10, 1.0, 0.92, "Lionel Messi", "Emiliano Martínez"),
    ("Argelia", "J", 68, 67, 64, 7, 4, 1.0, 1.00, "Riyad Mahrez", ""),
    ("Austria", "J", 70, 72, 69, 8, 4, 1.0, 1.00, "Christoph Baumgartner", ""),
    ("Jordania", "J", 56, 57, 56, 6, 2, 1.0, 1.00, "", ""),

    ("Portugal", "K", 86, 85, 82, 8, 8, 1.0, 0.96, "Cristiano Ronaldo", "Diogo Costa"),
    ("RD Congo", "K", 61, 61, 60, 7, 2, 1.0, 1.00, "", ""),
    ("Uzbekistán", "K", 58, 59, 60, 6, 2, 1.0, 1.00, "", ""),
    ("Colombia", "K", 83, 84, 81, 8, 6, 1.0, 1.00, "Luis Díaz", "Camilo Vargas"),

    ("Inglaterra", "L", 87, 86, 85, 8, 8, 1.0, 0.96, "Harry Kane", "Jordan Pickford"),
    ("Croacia", "L", 77, 82, 78, 6, 8, 1.0, 0.96, "Luka Modrić", "Dominik Livaković"),
    ("Ghana", "L", 62, 61, 59, 5, 5, 1.0, 1.00, "Mohammed Kudus", ""),
    ("Panamá", "L", 61, 63, 62, 6, 3, 1.0, 1.00, "", ""),
]

EQUIPOS = OrderedDict((fila[0], Equipo(*fila)) for fila in _DATOS)

GRUPOS = OrderedDict()
for _eq in EQUIPOS.values():
    GRUPOS.setdefault(_eq.grupo, []).append(_eq.nombre)

# Ajustes puntuales de fase de grupos: (equipo, rival) -> multiplicador de sus
# goles esperados. Yamal (isquios) se pierde los dos primeros partidos de España.
AJUSTES_GRUPOS = {
    ("España", "Cabo Verde"): 0.92,
    ("España", "Arabia Saudí"): 0.92,
}


def valoracion(nombre):
    """Valoración global, usada solo como último criterio de desempate."""
    eq = EQUIPOS[nombre]
    return eq.ataque + eq.medio + eq.defensa
