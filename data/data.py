import pandas as pd
from statsbombpy import sb
import numpy as np
import json
import os
import pymongo
pd.options.display.max_columns = None


def obtencionPartidosJornada(competition_id, season_id):
    
    partidos = sb.matches(competition_id=competition_id, season_id=season_id)
    partidos = partidos.sort_values('match_week')

    jornadas={}

    for index, partido in partidos.iterrows():
        nombre_partido = f'Matchday {partido.match_week}: {partido.home_team} {partido.home_score} - {partido.away_score} {partido.away_team}'
        identificador_partido = partido.match_id

        jornadas.update({nombre_partido: identificador_partido})

    return jornadas