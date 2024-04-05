import streamlit as st
import json
import pandas as pd
import numpy as np
import unicodedata
from dashboards import match_report, functions
from streamlit_option_menu import option_menu

def main():

    st.sidebar.markdown('## Select Competition')
    # Opciones de navegación
    selected_competition = st.sidebar.selectbox("Select a competition", ("LaLiga 2015/16", "Premier League 2015/16", "Serie A 2015/16", "Bundesliga 2015/16"))

    # Renderizar el dashboard seleccionado
    match_report.dashboardMatch(selected_competition)


if __name__ == '__main__':
    main()