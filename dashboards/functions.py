import streamlit as st
import pandas as pd 
from data import data
import json
import numpy as np
from streamlit_option_menu import option_menu
from mplsoccer import VerticalPitch,Pitch, Sbopen, FontManager, inset_image
from highlight_text import ax_text, fig_text
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import math
from urllib.request import urlopen

import matplotlib as mpl
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
from visualization.passing_network import draw_pitch, draw_pass_map
import matplotlib.pyplot as plt

import logging
logging.basicConfig(level=logging.DEBUG,  # Establece el nivel de registro
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mi_aplicacion')

white="white"
sbred='#e21017'
sblue="#0000FF"
lightgrey="#d9d9d9"
darkgrey='#9A9A9A'
cmaplist = [white, darkgrey, sbred]
cmap = LinearSegmentedColormap.from_list("", cmaplist)
# path effects
path_eff = [path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal()]

# Define una función para buscar el número del jugador por su nombre
def obtain_number_by_name(starting_xi, name):
    for player in starting_xi:
        if player['player']['name'] == name:
            return player['jersey_number']
    return None 


def _statsbomb_to_point(location, max_width=120, max_height=80):
    '''
    Convert a point's coordinates from a StatsBomb's range to 0-1 range.
    '''
    return location[0] / max_width, 1-(location[1] / max_height)

def passing_network_FoT(df, team_name):

    df = df.loc[df.team == team_name]
    print(df[df['type']=='Starting XI']['tactics_lineup'])
    team_lineup = df[df['type']=='Starting XI'].reset_index(drop=True)['tactics_lineup']
    # Extract the DataFrame for the specified team

    print(team_lineup)

    # Suponiendo que 'team_lineup' es una Serie y el primer elemento contiene la lista de jugadores
    team_lineup_list = team_lineup.iloc[0]

    # Ahora 'team_lineup_list' es una lista de diccionarios, puedes iterar sobre ella
    names_dict = {}
    for player in team_lineup_list:
        player_name = player['player']['name']
        player_nickname = player.get('player_nickname', player_name)  # Usando el nombre si no hay apodo
        names_dict[player_name] = player_nickname

    print(names_dict)

    print(df)
    df_events = df
    first_red_card_minute = df_events[df_events.foul_committed_card.isin(["Second Yellow", "Red Card"])].minute.min()
    first_substitution_minute = df_events[df_events.type == "Substitution"].minute.min()
    max_minute = df_events.minute.max()

    num_minutes = min(first_substitution_minute, first_red_card_minute, max_minute)

    plot_name = "statsbomb_match{0}_{1}".format("", team_name)

    ##opponent_team = [x for x in df_events.team.unique() if x != team_name][0]
    plot_title ="{0}'s passing network (StatsBomb eventing data)".format(team_name)

    plot_legend = "Location: pass origin\nSize: number of passes\nColor: number of passes"

    df_passes = df_events[(df_events.type == "Pass") &
                      (df_events.pass_outcome.isna()) &
                      (df_events.team == team_name) &
                      (df_events.minute < num_minutes)].copy()

    # If available, use player's nickname instead of full name to optimize space in plot
    df_passes["pass_recipient"] = df_passes.pass_recipient.apply(lambda x: names_dict[x] if names_dict[x] else x)
    df_passes["player_name"] = df_passes.player.apply(lambda x: names_dict[x] if names_dict[x] else x)

    df_passes["origin_pos_x"] = df_passes.location.apply(lambda x: _statsbomb_to_point(x)[0])
    df_passes["origin_pos_y"] = df_passes.location.apply(lambda x: _statsbomb_to_point(x)[1])
    player_position = df_passes.groupby("player_name").agg({"origin_pos_x": "median", "origin_pos_y": "median"})
    print(player_position)

    player_pass_count = df_passes.groupby("player_name").size().to_frame("num_passes")
    player_pass_value = df_passes.groupby("player_name").size().to_frame("pass_value")

    df_passes["pair_key"] = df_passes.apply(lambda x: "_".join(sorted([x["player_name"], x["pass_recipient"]])), axis=1)
    pair_pass_count = df_passes.groupby("pair_key").size().to_frame("num_passes")
    
    pair_pass_value = df_passes.groupby("pair_key").size().to_frame("pass_value")

    ax = draw_pitch()
    ax = draw_pass_map(ax, player_position, player_pass_count, player_pass_value,
              pair_pass_count, pair_pass_value, plot_title, plot_legend)
    plt.savefig("{0}.png".format(plot_name))
    fig = plt.show()

    #Centralization
    #calculate number of successful passes by player -> player_pass_count
    print(player_pass_count)
    #find one who made most passes
    max_no = player_pass_count["num_passes"].max()
    print(max_no)
    #calculate the denominator - 10*the total sum of passes
    denominator = 10*player_pass_count["num_passes"].sum()
    print(denominator)
    #calculate the nominator
    nominator = (max_no - player_pass_count['num_passes']).sum()
    print(nominator)
    #calculate the centralisation index
    centralisation_index = nominator/denominator
    print("Centralisation index is ", centralisation_index)

    return fig, ax, player_pass_count


def passing_network(df, team):
        
        team_name = team
        df = df.loc[df.team == team]
        print(df[df['type']=='Starting XI']['tactics_lineup'])
        starting_xi = df[df['type']=='Starting XI'].reset_index(drop=True)['tactics_lineup']
        df['dorsal'] = df['player'].apply(lambda x: obtain_number_by_name(starting_xi[0], x))
        sub = df.loc[df["type"] == "Substitution"].iloc[0]["index"]

        #make df with successfull passes by team until the first substitution and not throw-in
        mask = (df.pass_outcome.isnull()) & (df.pass_type != "Throw-in")
        sub_replacements = df.loc[df["type"] == 'Substitution', "substitution_replacement"].unique()

        df = df[(df['type']=='Pass')].copy()
        df[['x', 'y']] = df['location'].apply(pd.Series)
        df[['pass_end_x', 'pass_end_y']] = df['pass_end_location'].apply(pd.Series)

        #taking necessary columns
        df = df.loc[mask, ['x', 'y', 'pass_end_x', 'pass_end_y', "player", "pass_recipient", "dorsal"]]
        
        #Calculating vertices size and location
        players = df['player'].unique().tolist() 

        scatter_df = pd.DataFrame()
        
        for sub in sub_replacements:
            if sub in players:
                players.remove(sub)
                df = df.drop(df[(df.player == sub) | (df.pass_recipient == sub)].index)
                
        for i, name in enumerate(players):
            passx = df.loc[df["player"] == name]["x"].to_numpy()
            recx = df.loc[df["pass_recipient"] == name]["pass_end_x"].to_numpy()
            passy = df.loc[df["player"] == name]["y"].to_numpy()
            recy = df.loc[df["pass_recipient"] == name]["pass_end_y"].to_numpy()
            scatter_df.at[i, "player"] = name
            scatter_df['dorsal'] = scatter_df['player'].apply(lambda x: df.loc[df['player'] == x]['dorsal'].iloc[0])
            #make sure that x and y location for each circle representing the player is the average of passes and receptions
            scatter_df.at[i, "x"] = np.mean(np.concatenate([passx, recx]))
            scatter_df.at[i, "y"] = np.mean(np.concatenate([passy, recy]))
            #calculate number of passes
            scatter_df.at[i, "number_passes"] = df.loc[df["player"] == name].count().iloc[0]

        #adjust the size of a circle so that the player who made more passes
        scatter_df['marker_size'] = (scatter_df["number_passes"] / scatter_df["number_passes"].max() * 1500)

        #Calculating edges width
        #counting passes between players
        df["pair_key"] = df.apply(lambda x: "_".join(sorted([str(x["player"]), str(x["pass_recipient"])])), axis=1)

        lines_df = df.groupby(["pair_key"]).x.count().reset_index()
        lines_df.rename({'x':'pass_count'}, axis='columns', inplace=True)
        #setting a treshold. You can try to investigate how it changes when you change it.
        lines_df = lines_df[lines_df['pass_count']>3]
        
        #Plotting edges
        #plot once again pitch and vertices
        pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black',line_zorder=2)
        fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                            endnote_height=0.04, title_space=0, endnote_space=0)
        pitch.scatter(scatter_df.x, scatter_df.y, s=scatter_df.marker_size, color='red', edgecolors='grey', linewidth=1, alpha=1, ax=ax["pitch"], zorder = 3)

        # Agregar nombres a la leyenda
        legend_labels = []
        for i, row in scatter_df.iterrows():
            legend_labels.append(f'{int(row.dorsal)}: {row.player}')


        for i, row in scatter_df.iterrows():
            pitch.annotate(int(row.dorsal), xy=(row.x, row.y), c='black', va='center', ha='center', weight = "bold", size=16, ax=ax["pitch"], zorder = 4)

        for i, row in lines_df.iterrows():
                player1 = row["pair_key"].split("_")[0]
                player2 = row['pair_key'].split("_")[1]
                #take the average location of players to plot a line between them
                player1_x = scatter_df.loc[scatter_df["player"] == player1]['x'].iloc[0]
                player1_y = scatter_df.loc[scatter_df["player"] == player1]['y'].iloc[0]
                player2_x = scatter_df.loc[scatter_df["player"] == player2]['x'].iloc[0]
                player2_y = scatter_df.loc[scatter_df["player"] == player2]['y'].iloc[0]
                num_passes = row["pass_count"]
                #adjust the line width so that the more passes, the wider the line
                line_width = (num_passes / lines_df['pass_count'].max() * 10)
                #plot lines on the pitch
                pitch.lines(player1_x, player1_y, player2_x, player2_y,
                                alpha=1, lw=line_width, zorder=2, color="red", ax = ax["pitch"])
                

        fig.suptitle("Passing network "+team_name, fontsize = 30)

        df_table = scatter_df[['dorsal', 'player', 'number_passes']].copy()
        df_table['dorsal'] = df_table['dorsal'].astype(int)
        df_table['number_passes'] = df_table['number_passes'].astype(int)
        df_table = df_table.sort_values(by='number_passes', ascending=False).reset_index(drop=True)

        return fig, ax, df_table


def pass_map(df, menu_player):

    #Filtrando los pases solo del jugador seleccionado
    df_pass = df.loc[(df['player'] == menu_player) & (df['type'] == 'Pass')].copy()
    df_pass[['x', 'y']] = df_pass['location'].apply(pd.Series)
    df_pass[['pass_end_x', 'pass_end_y']] = df_pass['pass_end_location'].apply(pd.Series)
    comp = df_pass[df_pass['pass_outcome'].isnull()]
    incomp = df_pass[df_pass['pass_outcome'].notnull()]

    #dibujando el campo de futbol
    pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black',line_zorder=2)

    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('white')

    #Contando los pases por zona y coordenadas x & y de finalizacion de los pases para el mapa de calor
    bin_statistic = pitch.bin_statistic(comp.pass_end_x, comp.pass_end_y, statistic='count', bins=(12, 8), normalize=True)
    pitch.heatmap(bin_statistic, ax=ax, alpha=0.8, cmap=cmap)

    pitch.arrows(comp.x, comp.y,
    comp.pass_end_x, comp.pass_end_y, width=3,
    headwidth=8, headlength=5, color=sbred, ax=ax, zorder=2, label = "Completed pass")
    pitch.arrows(incomp.x, incomp.y,
    incomp.pass_end_x, incomp.pass_end_y, width=3,
    headwidth=8, headlength=5, color=darkgrey, ax=ax, zorder=2, label = "Incomplete pass")

    #etiquetas de color
    ax.legend(facecolor='white', handlelength=5, edgecolor='None', fontsize=20, loc='best')

    #titulo
    ax_title = ax.set_title('Pass Map', fontsize=30,color='black')
    
    #plt.show()
    return fig, ax

def ball_receipt_map():
    return 

def carry_map():
    return    

def pressure_map():
    return

def shot_map(df, menu_player):
        
    df_shot = df.loc[(df['player'] == menu_player) & (df['type'] == 'Shot')].copy()
    logger.debug(df_shot)
    if df_shot.empty:
        # Dibujar el campo sin flechas
        pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black', line_zorder=2)

        fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('white')

        # Etiquetas de color
        ax.legend(facecolor='white', handlelength=5, edgecolor='None', fontsize=20, loc='best')

        # Título
        ax_title = ax.set_title('Shot Map', fontsize=30, color='black')

        return fig, ax
    
    else:
        df_shot[['x', 'y']] = df_shot['location'].apply(pd.Series)
        df_shot[['shot_end_x', 'shot_end_y', 'shot_end_z']] = df_shot['shot_end_location'].apply(pd.Series)
        df_shot['shot_end_z'] = df_shot['shot_end_z'].fillna(0)
        comp = df_shot[(df_shot['shot_outcome']=='Saved')|(df_shot['shot_outcome']=='Saved to Post')|(df_shot['shot_outcome']=='Goal')]
        incomp = df_shot[(df_shot['shot_outcome']=='Off T')|(df_shot['shot_outcome']=='Saved Off T')]
        
        #dibujando el campo de futbol
        pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black',line_zorder=2)

        fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('white')

        pitch.arrows(comp.x, comp.y,
        comp.shot_end_x, comp.shot_end_y, width=3,
        headwidth=8, headlength=5, color=sbred, ax=ax, zorder=2, label = "Shot on target")
        pitch.arrows(incomp.x, incomp.y,
        incomp.shot_end_x, incomp.shot_end_y, width=3,
        headwidth=8, headlength=5, color=darkgrey, ax=ax, zorder=2, label = "Shot off target")

        #etiquetas de color
        ax.legend(facecolor='white', handlelength=5, edgecolor='None', fontsize=20, loc='best')

        #titulo
        ax_title = ax.set_title('Shot map', fontsize=30,color='black')
        
        return fig, ax
    

def lineup(matches, menu_game, team_name):

    game_id = matches.get(menu_game)
    parser = Sbopen()
    roboto_bold = FontManager(
        'https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf')
    path_eff = [path_effects.Stroke(linewidth=3, foreground='white'),
                path_effects.Normal()]

    parser = Sbopen()
    event, related, freeze, tactics = parser.event(game_id)
    # starting players
    starting_xi_event = event.loc[((event['type_name'] == 'Starting XI') &
                                (event['team_name'] == team_name)), ['id', 'tactics_formation']]
    # joining on the team name and formation to the lineup
    starting_xi = tactics.merge(starting_xi_event, on='id')

    # filter only succesful ball receipts from the starting XI
    event = event.loc[((event['type_name'] == 'Ball Receipt') &
                    (event['outcome_name'].isnull()) &
                    (event['player_id'].isin(starting_xi['player_id']))
                    ), ['player_id', 'x', 'y']]
    # merge on the starting positions to the events
    event = event.merge(starting_xi, on='player_id')
    formation = event['tactics_formation'].iloc[0]


    pitch = VerticalPitch(goal_type='box')
    fig, ax = pitch.draw(figsize=(6, 8.72))
    ax_text = pitch.formation(formation, positions=starting_xi.position_id, kind='text',
                            text=starting_xi.player_name.str.replace(' ', '\n'),
                            va='center', ha='center', fontsize=14, ax=ax)
    # scatter markers
    mpl.rcParams['hatch.linewidth'] = 0
    mpl.rcParams['hatch.color'] = sbred
    ax_scatter = pitch.formation(formation, positions=starting_xi.position_id, kind='scatter',
                                c=sbred, hatch='||', linewidth=3, s=500,
                                # you can also provide a single offset instead of a list
                                # for xoffset and yoffset
                                xoffset=-8,
                                ax=ax)
    
    return fig, ax

def heatMap(df, menu_player):
    df_player = df.loc[df.player == menu_player]
    df_player[['x', 'y']] = df_player['location'].apply(pd.Series)
    
    pitch = Pitch(pitch_type='statsbomb', pitch_color='white', line_color='black',line_zorder=2)

    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('white')

    bin_statistic = pitch.bin_statistic(df_player.x, df_player.y, statistic='count', bins=(10, 6), normalize=True)
    pitch.heatmap(bin_statistic, ax=ax, alpha=0.8, cmap=cmap)
    labels = pitch.label_heatmap(bin_statistic, color='#f4edf0', fontsize=18,
                             ax=ax, ha='center', va='center',
                             str_format='{:.0%}', path_effects=path_eff)

    #titulo
    ax_title = ax.set_title('Heatmap', fontsize=30,color='black')

    return fig, ax