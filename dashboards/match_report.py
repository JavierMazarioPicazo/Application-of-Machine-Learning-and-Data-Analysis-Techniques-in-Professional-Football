import streamlit as st
import pandas as pd 
from data import data
import json
import numpy as np
from streamlit_option_menu import option_menu
from mplsoccer import VerticalPitch,Pitch
from highlight_text import ax_text, fig_text
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from dashboards import functions as fs
import re

with open('./games_json/badges/badges.json', 'r') as archivo_json:
    badge_urls = json.load(archivo_json)


def dashboardMatch(selected_competition):

     # Título de la aplicación
    st.title("Match report")
    st.markdown("""
    
    """)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    if selected_competition == "LaLiga 2015/16":
        matches = data.obtencionPartidosJornada(11, 27)
        route='LaLiga15/'
    elif selected_competition == "Premier League 2015/16":
        matches = data.obtencionPartidosJornada(2, 27)
        route='Premier15/'
    elif selected_competition == "Serie A 2015/16":
        matches = data.obtencionPartidosJornada(12, 27)
        route='SerieA15/'
    elif selected_competition == "Bundesliga 2015/16":
        matches = data.obtencionPartidosJornada(9, 27)
        route='Bundesliga15/'
    else:
        st.error("Invalid competition selection!")

    matchdays_list = list(set([game.split(":")[0] for game in matches.keys()]))

    # Ordenar por el número de jornada
    matchdays_list.sort(key=lambda x: int(x.split(' ')[1]))
    games_list = list(matches.keys())
    games_id_list = list(matches.values())

    st.sidebar.markdown('## Select Matchday')
    # Seleccionar la jornada
    selected_matchday = st.sidebar.selectbox('Select Matchday', matchdays_list, index=0)

    # Filtrar partidos basándose en la jornada seleccionada
    filtered_games = [game for game in games_list if game.split(":")[0] == selected_matchday]

    # Mostrar los partidos filtrados en otro desplegable
    menu_game = st.sidebar.selectbox('Select Game', filtered_games, index=0)


    ##st.sidebar.markdown('## Select Football Game')
    ##menu_game = st.sidebar.selectbox('Select Game', games_list, index=0)


    # Read JSON file based on selected game
    filename = './games_json/'+route+str(matches.get(menu_game))+'.json'
    with open(filename, 'r', errors="ignore") as f:
        game = json.load(f)
    df = pd.json_normalize(game, sep='_')


    # Replace non-unicode characters in players names
    df['player'] = df['player'].astype(str)
    df['player'] = df['player'].replace('nan', np.nan)


    # Get teams and players names
    team_1 = df['team'].unique()[0]
    team_2 = df['team'].unique()[1]
    mask_1 = df.loc[df['team'] == team_1]
    mask_2 = df.loc[df['team'] == team_2]
    player_names_1 = mask_1['player'].dropna().unique()
    player_names_2 = mask_2['player'].dropna().unique()

    # Mostrar los escudos de los equipos en la misma línea
    col1, col2, col3 = st.columns(3)
    with col1:
        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol2:
            st.image(badge_urls.get(team_1), caption=team_1, width=100)
    with col2:
        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol2:
            numbers = re.findall(r'\d+', menu_game)
            game_result = numbers[1] + " - " + numbers[2]
            st.markdown(f"<p></p><h2 style='text-align: center;'>{game_result}</h2>", unsafe_allow_html=True)
    with col3:
        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol2:
            st.image(badge_urls.get(team_2), caption=team_2, width=100)

    col1, col2 = st.columns(2)
    with col1:
        fig_lineup, ax = fs.lineup(matches, menu_game, team_1)
        st.pyplot(fig_lineup)
    with col2:
        fig_lineup1, ax = fs.lineup(matches, menu_game, team_2)
        st.pyplot(fig_lineup1)

    # Drop-down menus 'Select Team, Player and Activity'
    st.markdown('### Select Team and Player')
    st.write("""Use dropdown-menus to select a game, team, player, and activity. 
    Statistics plot will appear on the pitch below.""")
    menu_team = st.selectbox('Select Team', (team_1, team_2))
    if menu_team == team_1:
        menu_player = st.selectbox('Select Player', player_names_1, index=1)
    else:
        menu_player = st.selectbox('Select Player', player_names_2, index=1)

    # List of activities for drop-down menus
    activities = ['Pass', 'Heatmap', 'Shot', 'Passing Network']


    selected2 = st.selectbox('Select Function', (activities))
    
    # Get plot function based on selected activity
    if selected2 == 'Pass':
        st.write('###', selected2)
        st.write('######', menu_game)
        st.write('###### Player:', menu_player, '(', menu_team, ')')
        fig, ax = fs.pass_map(df, menu_player)
        st.pyplot(fig)
    elif selected2 == 'Heatmap':
        st.write('###', selected2)
        st.write('######', menu_game)
        st.write('###### Player:', menu_player, '(', menu_team, ')')
        fig, ax = fs.heatMap(df, menu_player)
        st.pyplot(fig)
    elif selected2 == 'Shot':
        st.write('###', selected2)
        st.write('######', menu_game)
        st.write('###### Player:', menu_player, '(', menu_team, ')')
        fig, ax = fs.shot_map(df, menu_player)
        st.pyplot(fig)
    elif selected2 == 'Passing Network':
        ##fig_network, ax, df_table = fs.passing_network(df, menu_team)
        fig_network, ax, player_pass_count = fs.passing_network_FoT(df, menu_team)
        st.pyplot(fig_network)
        st.table(player_pass_count)
        