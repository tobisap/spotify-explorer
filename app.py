import streamlit as st
import pandas as pd
import plotly.express as px
import ast

# --- Konfiguration & Design ---
st.set_page_config(
    page_title="Spotify Musik-Explorer",
    page_icon="🎵",
    layout="wide"
)

# CSS für den Spotify Dark Mode
spotify_dark_mode_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
body, .main { 
    background-color: #121212; 
    font-family: 'Montserrat', sans-serif; 
    color: #FFFFFF; 
}
h1 {
    font-weight: 900;
    background: -webkit-linear-gradient(45deg, #1DB954, #FFFFFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.st-emotion-cache-16txtl3 { 
    background-color: #040404; 
    border-right: 1px solid #282828; 
}
.st-emotion-cache-16txtl3 .st-emotion-cache-1y4p8pa { 
    color: #1DB954 !important; 
    font-weight: 700; 
}
.st-emotion-cache-134d5h5 { background-color: #535353; }
.st-emotion-cache-1ft0j9a { background-color: #1DB954; }
.st-emotion-cache-1b0g02j { 
    background-color: #282828; 
    border-radius: 8px; 
    padding: 1rem; 
}
.stLinkButton>a, .stButton>button {
    background-color: #1DB954; color: #FFFFFF !important; border-radius: 500px;
    padding: 10px 25px; font-weight: 700; border: none; text-decoration: none;
    display: inline-block; text-align: center;
}
.stLinkButton>a:hover, .stButton>button:hover { background-color: #1ED760; color: #FFFFFF !important; }
</style>
"""
st.markdown(spotify_dark_mode_css, unsafe_allow_html=True)


# --- Daten laden und bereinigen ---
@st.cache_data
def load_data():
    """Lädt die Parquet-Datei und bereinigt die Daten."""
    try:
        df = pd.read_parquet('data_final.parquet')
    except FileNotFoundError:
        st.error("FEHLER: Die Datei 'data_final.parquet' wurde nicht gefunden.")
        return pd.DataFrame()

    numeric_cols = ['year', 'danceability', 'popularity', 'tempo', 'energy', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)

    if 'year' in df.columns:
        df['year'] = df['year'].astype(int)
        df['decade'] = (df['year'] // 10) * 10
        
    if 'artists' in df.columns:
        df['display_artists'] = df['artists'].str.replace(r"\[|\]|'", "", regex=True)
    else:
        df['display_artists'] = "N/A"
        
    return df

df = load_data()


# --- Seiten-Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Wähle eine Seite", ["Musik-Explorer", "Song-Quiz"], key="page_select")


# ====================================================================================================
# SEITE 1: MUSIK-EXPLORER
# ====================================================================================================
if page == "Musik-Explorer":
    st.title("Spotify Musik-Explorer")

    if df.empty:
        st.info("Keine ladbaren Daten gefunden. Bitte die Datei überprüfen.")
        st.stop()

    # --- Seitenleiste mit Filtern ---
    st.sidebar.header("Filter")
    search_term = st.sidebar.text_input("Song- oder Künstlersuche", key="song_search")

    filtered_df = df.copy()

    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['display_artists'].str.contains(search_term, case=False, na=False)
        ]

    if 'decade' in filtered_df.columns and len(filtered_df['decade'].unique()) > 1:
        decades = sorted(filtered_df['decade'].unique())
        decade_options = [f"{decade}er" for decade in decades]
        start_decade_str, end_decade_str = st.sidebar.select_slider(
            "Jahrzehnt", options=decade_options, 
            value=(decade_options[0], decade_options[-1]), key="decade_slider"
        )
        start_decade = int(start_decade_str.replace('er', ''))
        end_decade = int(end_decade_str.replace('er', ''))
        filtered_df = filtered_df[(filtered_df['decade'] >= start_decade) & (filtered_df['decade'] <= end_decade)]

    if 'danceability' in filtered_df.columns:
        dance_range = st.sidebar.slider("Tanzbarkeit (0-100)", 0, 100, (0, 100), key="dance_slider")
        filtered_df = filtered_df[(filtered_df['danceability'] >= dance_range[0]/100.0) & (filtered_df['danceability'] <= dance_range[1]/100.0)]

    if 'popularity' in filtered_df.columns:
        val = st.sidebar.slider("Popularität", 0, 100, (0, 100), key="pop_slider")
        filtered_df = filtered_df[(filtered_df['popularity'] >= val[0]) & (filtered_df['popularity'] <= val[1])]

    if 'tempo' in filtered_df.columns:
        min_t, max_t = int(df['tempo'].min()//5*5), int(df['tempo'].max()//5*5)+5
        val = st.sidebar.slider("Tempo (BPM)", min_t, max_t, (min_t, max_t), step=5, key="tempo_slider")
        filtered_df = filtered_df[(filtered_df['tempo'] >= val[0]) & (filtered_df['tempo'] <= val[1])]

    # --- Haupt-Ansicht auf der Seite ---
    st.header(f"Gefilterte Ergebnisse")

    if filtered_df.empty:
        st.warning("Keine Songs für die aktuelle Filterkombination gefunden.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Songs gefunden", f"{len(filtered_df)}")
        col2.metric("Ø Energie", f"{filtered_df['energy'].mean():.2f}")
        col3.metric("Ø Positivität", f"{filtered_df['valence'].mean():.2f}")
        
        st.subheader("Dynamische Analyse")
        axis_options_german = {'danceability': 'Tanzbarkeit', 'energy': 'Energie', 'tempo': 'Tempo', 'popularity': 'Popularität', 'valence': 'Positivität', 'year': 'Jahr'}
        col_x, col_y = st.columns(2)
        with col_x:
            x_axis_german = st.selectbox("X-Achse:", options=list(axis_options_german.values()), index=3, key="xaxis_select")
        with col_y:
            y_axis_german = st.selectbox("Y-Achse:", options=list(axis_options_german.values()), index=1, key="yaxis_select")
        x_axis = [key for key, value in axis_options_german.items() if value == x_axis_german][0]
        y_axis = [key for key, value in axis_options_german.items() if value == y_axis_german][0]
        
        st.subheader(f"{x_axis.capitalize()} vs. {y_axis.capitalize()}")
        fig = px.scatter(
            filtered_df, x=x_axis, y=y_axis, color="popularity",
            color_continuous_scale=["#FFFFFF", "#1DB954"],
            size="popularity", size_max=60, hover_name="name"
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#273126", font_color="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Song-Details und Player")
        sorted_songs = filtered_df.sort_values(by='popularity', ascending=False)
        sorted_songs['display_option'] = sorted_songs['name'] + ' – ' + sorted_songs['display_artists']
        song_list = [""] + sorted_songs['display_option'].tolist()
        selected_option = st.selectbox("Wähle einen Song:", options=song_list, key="song_select_explorer")
        
        if selected_option:
            selected_song = sorted_songs[sorted_songs['display_option'] == selected_option].iloc[0]
            link_col = 'Link' if 'Link' in selected_song and pd.notna(selected_song['Link']) else 't' if 't' in selected_song and pd.notna(selected_song['t']) else None
            if link_col:
                try:
                    track_id = selected_song[link_col].split('/track/')[-1].split('?')[0]
                    embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
                    st.components.v1.iframe(embed_url, height=80)
                except:
                    st.warning("Der Spotify-Link für diesen Song scheint ungültig zu sein.")
            else:
                st.warning("Kein Spotify-Link für diesen Song verfügbar.")

# ====================================================================================================
# SEITE 2: SONG-QUIZ
# ====================================================================================================
elif page == "Song-Quiz":
    st.title("🎵 Song-Quiz")
    st.info("Höre dir den Song an und schätze seine Eigenschaften. Je näher du liegst, desto mehr Punkte bekommst du!")

    # --- Hilfsfunktionen für Highscore ---
    @st.cache_data
    def load_highscores():
        try:
            return pd.read_csv("highscores.csv")
        except FileNotFoundError:
            return pd.DataFrame(columns=["Name", "Score"])

    def save_highscore(name, score):
        df_scores = load_highscores()
        new_entry = pd.DataFrame([[name, score]], columns=["Name", "Score"])
        df_scores = pd.concat([df_scores, new_entry], ignore_index=True)
        df_scores = df_scores.sort_values(by="Score", ascending=False).head(5)
        df_scores.to_csv("highscores.csv", index=False)
        st.cache_data.clear() # Cache leeren, damit die neue Punktzahl geladen wird

    # --- Initialisierung des Spielzustands ---
    if 'round' not in st.session_state:
        st.session_state.round = 0
        st.session_state.score = 0
        st.session_state.song_history = []
        st.session_state.guess_submitted = False

    def next_song():
        available_songs = df[~df.index.isin(st.session_state.song_history)]
        if not available_songs.empty:
            st.session_state.current_song = available_songs.sample(1)
            st.session_state.song_history.append(st.session_state.current_song.index[0])
            st.session_state.round += 1
            st.session_state.guess_submitted = False
        else:
            st.session_state.round = 6

    def restart_game():
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    # --- Spiel-Logik ---
    if st.session_state.get('round', 0) == 0:
        if st.button("Neues Spiel starten"):
            st.session_state.round = 0 # Zurücksetzen vor dem Start
            st.session_state.score = 0
            st.session_state.song_history = []
            next_song()
            st.rerun()

    elif 1 <= st.session_state.get('round', 0) <= 5:
        st.header(f"Runde {st.session_state.round} von 5 | Punktzahl: {st.session_state.score}")
        
        song = st.session_state.current_song.iloc[0]
        
        link_col = 'Link' if 'Link' in song and pd.notna(song['Link']) else 't' if 't' in song and pd.notna(song['t']) else None
        if link_col:
            try:
                track_id = song[link_col].split('/track/')[-1].split('?')[0]
                embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
                st.components.v1.iframe(embed_url, height=80)
            except:
                st.warning("Link ungültig, nächster Song wird geladen...")
                next_song()
                st.rerun()
        else:
            st.warning("Kein Link verfügbar, nächster Song wird geladen...")
            next_song()
            st.rerun()

        if not st.session_state.get('guess_submitted', False):
            with st.form(key="guess_form"):
                st.subheader("Deine Schätzung:")
                guess_dance = st.slider("Tanzbarkeit (0-100)", 0, 100, 50)
                guess_energy = st.slider("Energie (0-100)", 0, 100, 50)
                guess_valence = st.slider("Positivität (0-100)", 0, 100, 50)
                submit_button = st.form_submit_button(label='Schätzung abgeben')

                if submit_button:
                    st.session_state.guess_submitted = True
                    actual_dance = int(song['danceability'] * 100)
                    actual_energy = int(song['energy'] * 100)
                    actual_valence = int(song['valence'] * 100)
                    score_dance = max(0, 100 - abs(actual_dance - guess_dance))
                    score_energy = max(0, 100 - abs(actual_energy - guess_energy))
                    score_valence = max(0, 100 - abs(actual_valence - guess_valence))
                    round_score = int((score_dance + score_energy + score_valence) / 3)
                    st.session_state.score += round_score
                    
                    st.session_state.last_results = (actual_dance, guess_dance, actual_energy, guess_energy, actual_valence, guess_valence, round_score)
                    st.rerun()
        
        if st.session_state.get('guess_submitted', False):
            actual_dance, guess_dance, actual_energy, guess_energy, actual_valence, guess_valence, round_score = st.session_state.last_results
            st.subheader("Auswertung der Runde")
            col1, col2, col3 = st.columns(3)
            col1.metric("Tanzbarkeit", f"Echt: {actual_dance}", f"Du: {guess_dance}")
            col2.metric("Energie", f"Echt: {actual_energy}", f"Du: {guess_energy}")
            col3.metric("Positivität", f"Echt: {actual_valence}", f"Du: {guess_valence}")
            st.success(f"Du hast in dieser Runde {round_score} Punkte erhalten!")
            
            if st.button("Nächster Song"):
                next_song()
                st.rerun()
                
    else: # Spielende
        st.header(f"Spiel beendet! Deine Gesamtpunktzahl: {st.session_state.score}")
        with st.form(key="highscore_form"):
            name = st.text_input("Gib deinen Namen für die Highscore-Liste ein:")
            submit_highscore = st.form_submit_button("Highscore speichern")
            if submit_highscore:
                if name:
                    save_highscore(name, st.session_state.score)
                    st.success("Highscore gespeichert!")
                else:
                    st.error("Bitte gib einen Namen ein.")
        
        if st.button("Nochmal spielen"):
            restart_game()
            st.rerun()

    st.markdown("---")
    st.header("🏆 Highscores")
    st.table(load_highscores())
