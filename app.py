import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# --- Konfiguration & Design ---
st.set_page_config(
    page_title="Spotify Musik-Explorer & Quiz",
    page_icon="🎵",
    layout="wide"
)

# CSS für den Spotify Dark Mode (unverändert)
spotify_dark_mode_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&display=swap');
body, .main { 
    background-color: #121212; 
    font-family: 'Outfit', sans-serif; 
    color: #FFFFFF; 
}
h1, h2, h3 {
    font-weight: 700;
    color: #FFFFFF;
}

[data-testid="stMetric"] {
    background-color: #131313;
    border: 1px solid #131313;
    border-radius: 10px;
    padding: 1rem;
    font-family: 'Outfit'
}

h1 {
    font-weight: 800;
    background: -webkit-linear-gradient(45deg, #1DB954, #FFFFFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    border-bottom: 1px solid #535353;
    padding-bottom: 4rem;
}
.st-emotion-cache-16txtl3 { 
    background-color: #040404; 
    border-right: 1px solid #282828; 
}
.st-emotion-cache-16txtl3 .st-emotion-cache-1y4p8pa { 
    color: #1DB954 !important; 
    font-weight: 400; 
}
.st-emotion-cache-134d5h5 { background-color: #535353; }
.st-emotion-cache-1ft0j9a { background-color: #1DB954; }
.st-emotion-cache-1b0g02j { 
    background-color: #282828; 
    border-radius: 8px; 
    padding: 1rem; 
}
.stButton>button {
    background-color: #1DB954;
    color: #FFFFFF;
    border-radius: 500px;
    padding: 10px 25px;
    font-weight: 400;
    border: none;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}
.stButton>button:hover {
    background-color: #1ED760;
    color: #FFFFFF !important;
    border: none;
}
/* --- Modernes Slider-Design --- */

/* Hauptcontainer des Sliders */
[data-testid="stSlider"] {
    padding-top: 5px;
}

/* Der Schieberegler-Balken (Track) für Webkit-Browser (Chrome, Safari) */
[data-testid="stSlider"] .st-emotion-cache-134d5h5 {
    background: #444444; /* Dunkelgrauer Balken */
    height: 4px; /* Dünnerer Balken */
    border-radius: 2px;
}

/* Der farbige Teil des Balkens (Fill) */
[data-testid="stSlider"] .st-emotion-cache-1ft0j9a {
    background: #1DB954; /* Spotify-Grün */
    height: 4px;
    border-radius: 2px;
}

/* Der runde Anfasser (Thumb) für Webkit-Browser */
[data-testid="stSlider"] .st-emotion-cache-134d5h5::-webkit-slider-thumb {
    -webkit-appearance: none; /* Standard-Aussehen entfernen */
    appearance: none;
    width: 30px; /* Größe des Anfassers */
    height: 30px;
    border-radius: 50%; /* Rund machen */
    background: #FFFFFF; /* Weißer Anfasser */
    cursor: pointer;
    margin-top: -8px; /* Zentriert den Anfasser auf dem dünnen Balken */
    box-shadow: 0 1px 3px rgba(0,0,0,0.3); /* Leichter Schatten */
    transition: transform 0.1s ease-in-out; /* Sanfte Animation */
}

/* Leichte Vergrößerung beim Klicken */
[data-testid="stSlider"] .st-emotion-cache-134d5h5::-webkit-slider-thumb:active {
    transform: scale(1.3);
}

/* Dasselbe für Mozilla Firefox */
[data-testid="stSlider"] .st-emotion-cache-134d5h5::-moz-range-thumb {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #FFFFFF;
    cursor: pointer;
    border: none;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
</style>
"""
st.markdown(spotify_dark_mode_css, unsafe_allow_html=True)


# --- DATENLADEN ---
@st.cache_data
def load_data():
    """Lädt die Parquet-Datei und bereinigt die Daten."""
    try:
        df = pd.read_parquet('data_final.parquet')
    except FileNotFoundError:
        st.error("FEHLER: Die Datei 'data_final.parquet' wurde nicht gefunden.")
        return None

    # Sicherstellen, dass die Link-Spalte existiert (t oder Link)
    if 't' in df.columns:
        df.rename(columns={'t': 'link'}, inplace=True)
    elif 'Link' in df.columns:
        df.rename(columns={'Link': 'link'}, inplace=True)
    else:
        # Fallback, falls keine der Spalten da ist
        st.error("FEHLER: Weder 't' noch 'Link' als Spalte für den Spotify-Track gefunden.")
        return None
        
    df.dropna(subset=['link'], inplace=True) # Songs ohne Link entfernen

    numeric_cols = ['year', 'danceability', 'popularity', 'tempo', 'energy', 'valence', 'duration_ms']
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
        
    if 'duration_ms' in df.columns:
        df['duration_s'] = df['duration_ms'] / 1000
        df.dropna(subset=['duration_s'], inplace=True)
        
    return df

df = load_data()

# --- HIGHSCORE FUNKTIONEN ---
HIGHSCORE_FILE = "highscores.json"

def load_highscores():
    """Lädt Highscores aus einer JSON-Datei."""
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_highscores(scores):
    """Speichert Highscores in einer JSON-Datei."""
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

# --- SEITEN DEFINITIONEN ---

def explorer_page(df_explorer):
    """Rendert die Explorer-Seite."""
    st.title("Spotify Musik-Explorer")
    
    if df_explorer.empty:
        st.info("Keine ladbaren Daten gefunden. Bitte die Datei überprüfen.")
        return

    # --- SEITENLEISTE MIT FILTERN ---
    st.sidebar.header("Filter für Explorer")
    search_term = st.sidebar.text_input("Song- oder Künstlersuche", key="song_search")

    filtered_df = df_explorer.copy()
    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['display_artists'].str.contains(search_term, case=False, na=False)
        ]

    if 'decade' in filtered_df.columns and len(filtered_df['decade'].unique()) > 1:
        decades = sorted(filtered_df['decade'].unique())
        decade_options = [f"{decade}er" for decade in decades]
        start_decade_str, end_decade_str = st.sidebar.select_slider(
            "Jahrzehnt", 
            options=decade_options, 
            value=(decade_options[0], decade_options[-1]),
            key="decade_slider"
        )
        start_decade = int(start_decade_str.replace('er', ''))
        end_decade = int(end_decade_str.replace('er', ''))
        filtered_df = filtered_df[(filtered_df['decade'] >= start_decade) & (filtered_df['decade'] <= end_decade)]

    # Hier werden die fehlenden Filter für Tanzbarkeit, Popularität und Tempo hinzugefügt.
    dance_range = st.sidebar.slider(
        "Tanzbarkeit", 
        min_value=0, max_value=100, value=(0, 100)
    )

    # Wende die Skalierungsformel an, um die Daten auf den 0-100 Bereich zu bringen
    scaled_danceability = (filtered_df['danceability'] / 1_000) * 100

    # NEU: Werte, die über 100 liegen, auf 100 setzen
    scaled_danceability = scaled_danceability.clip(upper=100)

    # Führe den Filter auf den skalierten und begrenzten Werten durch
    filtered_df = filtered_df[
        (scaled_danceability >= dance_range[0]) & 
        (scaled_danceability <= dance_range[1])
    ]

    popularity_range = st.sidebar.slider(
        "Popularität", 
        min_value=0, max_value=100, value=(0, 100)
    )
    filtered_df = filtered_df[
        (filtered_df['popularity'] >= popularity_range[0]) & 
        (filtered_df['popularity'] <= popularity_range[1])
    ]

    tempo_range = st.sidebar.slider(
        "Tempo (BPM)", 
        min_value=int(df_explorer['tempo'].min()), 
        max_value=int(df_explorer['tempo'].max()), 
        value=(int(df_explorer['tempo'].min()), int(df_explorer['tempo'].max()))
    )
    filtered_df = filtered_df[
        (filtered_df['tempo'] >= tempo_range[0]) & 
        (filtered_df['tempo'] <= tempo_range[1])
    ]
    
    if 'duration_s' in filtered_df.columns and not filtered_df.empty:
        # Der dynamische Maximalwert wird beibehalten
        max_duration = int(filtered_df['duration_s'].max())
    
        # Stellen Sie sicher, dass der Maximalwert größer als der Startwert ist
        if max_duration > 85:
            duration_range = st.sidebar.slider(
                "Liedlänge (Sekunden)",
                min_value=85,  # ANPASSUNG: Start bei 85 Sekunden
                max_value=465,
                value=(85, 465), # ANPASSUNG: Standardbereich beginnt bei 85
                step=5  # ANPASSUNG: Schritte in 5-Sekunden-Intervallen
            )
            filtered_df = filtered_df[
                (filtered_df['duration_s'] >= duration_range[0]) & 
                (filtered_df['duration_s'] <= duration_range[1])
            ]
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.header(f"Ergebnisse")
    if filtered_df.empty:
        st.warning("Keine Songs für die aktuelle Filterkombination gefunden.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Songs gefunden", f"{len(filtered_df)}")
        col2.metric("Ø Energie", f"{filtered_df['energy'].mean():.2f}")
        col3.metric("Ø Positivität", f"{filtered_df['valence'].mean():.2f}")

        # --- Interaktive Grafiken etc. ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Dynamische Analyse")
        axis_options_german = {
            'danceability': 'Tanzbarkeit', 'energy': 'Energie', 'tempo': 'Tempo',
            'popularity': 'Popularität', 'valence': 'Positivität', 'year': 'Jahr'
        }
        col_x, col_y = st.columns(2)
        x_axis_key = col_x.selectbox("X-Achse:", options=list(axis_options_german.keys()), format_func=lambda x: axis_options_german[x], index=3)
        y_axis_key = col_y.selectbox("Y-Achse:", options=list(axis_options_german.keys()), format_func=lambda x: axis_options_german[x], index=1)
        
        fig = px.scatter(filtered_df, x=x_axis_key, y=y_axis_key, color="popularity",
                         color_continuous_scale=["#FFFFFF", "#1DB954"], size="popularity", size_max=60,
                         hover_name="name", hover_data=['display_artists'])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#131313", font_color="#FFFFFF", height=600)
        st.plotly_chart(fig, use_container_width=True)

        # --- Song-Auswahl und Player ---
        st.subheader("Song-Details und Player")
        sorted_songs = filtered_df.sort_values(by='popularity', ascending=False)
        sorted_songs['display_option'] = sorted_songs['name'] + ' – ' + sorted_songs['display_artists']
        song_list = [""] + sorted_songs['display_option'].tolist()
        selected_option = st.selectbox("Wähle einen Song:", options=song_list, key="song_select")

        if selected_option:
            selected_song = sorted_songs[sorted_songs['display_option'] == selected_option].iloc[0]
            track_id = selected_song['link'].split('/track/')[-1].split('?')[0]
            embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
            st.components.v1.iframe(embed_url, height=200) # Haupt-Player

            # --- NEU: ANZEIGE DER SONG-ATTRIBUTE IN KACHELN ---
            st.markdown("---")
            st.subheader("Musikalische Eigenschaften")

            # Annahme: Tanzbarkeit, Energie und Valenz sind in den Daten auf einer Skala von 0-1000
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Tanzbarkeit 💃", value=f"{int(selected_song.get('danceability', 0) / 10)}%")
            with col2:
                st.metric(label="Energie ⚡", value=f"{int(selected_song.get('energy', 0) / 10)}%")
            with col3:
                st.metric(label="Positivität 😊", value=f"{int(selected_song.get('valence', 0) / 10)}%")

            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(label="Tempo 👟", value=f"{int(selected_song.get('tempo', 0))} BPM")
            with col5:
                st.metric(label="Popularität 🔥", value=f"{selected_song.get('popularity', 0)} / 100")
            with col6:
                st.metric(label="Jahr 📅", value=f"{selected_song.get('year', 'N/A')}")

        st.markdown("---")
        st.write("") 
        with st.expander("Korrelations-Heatmap anzeigen"):
            st.markdown("""
            Diese Heatmap zeigt, wie stark die verschiedenen musikalischen Eigenschaften in den gefilterten Songs zusammenhängen. 
            Werte nahe **1** deuten auf eine starke *positive* Korrelation hin, während Werte nahe **-1** auf eine starke *negative* Korrelation hindeuten. Werte um **0** bedeuten keinen klaren Zusammenhang.
            """)

            # Auswahl der relevanten numerischen Spalten für die Korrelation
            corr_columns_keys = ['popularity', 'year', 'danceability', 'energy', 'valence', 'tempo']
            existing_corr_columns = [col for col in corr_columns_keys if col in filtered_df.columns]
    
            if len(existing_corr_columns) > 1:
                # Deutsche Labels für die Achsen verwenden
                german_labels = [axis_options_german.get(key, key) for key in existing_corr_columns]
        
                # Korrelationsmatrix berechnen und Spalten/Index umbenennen
                corr_matrix = filtered_df[existing_corr_columns].corr()
                corr_matrix.columns = german_labels
                corr_matrix.index = german_labels
    
                # Heatmap mit Plotly Express erstellen
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=".2f",  # Werte in den Zellen anzeigen (auf 2 Dezimalstellen)
                    aspect="auto",
                    color_continuous_scale="Greens", # Farbskala passend zum Spotify-Theme
                    labels=dict(color="Korrelation")
                )
        
                # Layout an das Dark-Mode-Theme anpassen
                fig_corr.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#131313",
                    font_color="#FFFFFF"
                )
        
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.warning("Nicht genügend Daten vorhanden, um eine Korrelationsmatrix zu erstellen.")


def game_page(df_game):
    """Rendert die Spiel-Seite."""
    st.title("Song-Quiz: Wie gut kennst du die Musik?")
    st.write("") 
    st.markdown("Höre einen zufälligen Song und schätze seine Eigenschaften. Je näher du liegst, desto mehr Punkte bekommst du!")

    # Initialisiere den Spielzustand
    if 'game_round' not in st.session_state:
        st.session_state.game_round = 0
        st.session_state.total_score = 0
        st.session_state.high_scores = load_highscores()
        st.session_state.current_song = None
        st.session_state.guess_submitted = False

    # --- SPIELSTEUERUNG ---
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.game_round == 0:
            if st.button("Neues Spiel starten!"):
                st.session_state.game_round = 1
                st.session_state.total_score = 0
                st.session_state.current_song = df_game.sample(1).iloc[0]
                st.session_state.guess_submitted = False
                st.rerun()
        elif st.session_state.game_round <= 5:
            st.subheader(f"Runde {st.session_state.game_round} von 5 | Gesamtscore: {st.session_state.total_score}")
        else: # Spielende
            st.header(f"Spiel beendet! Dein finaler Score: {st.session_state.total_score}")
            
            with st.form("highscore_form"):
                player_name = st.text_input("Gib deinen Namen für die Highscore-Liste ein:", max_chars=15)
                submit_button = st.form_submit_button("Highscore speichern")

                if submit_button and player_name:
                    new_score = {'name': player_name, 'score': st.session_state.total_score}
                    st.session_state.high_scores.append(new_score)
                    st.session_state.high_scores = sorted(st.session_state.high_scores, key=lambda x: x['score'], reverse=True)[:5]
                    save_highscores(st.session_state.high_scores)
                    st.success(f"Dein Score wurde gespeichert, {player_name}!")
                    st.balloons()
            
            if st.button("Nochmal spielen?"):
                st.session_state.game_round = 0 # Setzt das Spiel zurück
                st.rerun()


    # --- HIGHSCORE-ANZEIGE ---
    with col2:
        st.subheader("🏆 Highscores")
        if not st.session_state.high_scores:
            st.write("Noch keine Highscores.")
        else:
            for i, score in enumerate(st.session_state.high_scores):
                st.markdown(f"**{i+1}. {score['name']}**: {score['score']} Punkte")

    st.markdown("---")

    # --- SPIELABLAUF ---
    if 1 <= st.session_state.game_round <= 5:
        song = st.session_state.current_song
        
        # Spotify Player anzeigen
        try:
            track_id = song['link'].split('/track/')[-1].split('?')[0]
            embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
            st.components.v1.iframe(embed_url, height=152)
        except Exception:
            st.error("Song konnte nicht geladen werden. Nächste Runde wird gestartet.")
            # Nächste Runde erzwingen
            st.session_state.current_song = df_game.sample(1).iloc[0]
            st.rerun()

        st.markdown("### Deine Schätzung:")

        if not st.session_state.guess_submitted:
            with st.form("guess_form"):
                guess_dance = st.slider("Tanzbarkeit", 0, 100, 50)
                guess_energy = st.slider("Energie", 0, 100, 50)
                guess_valence = st.slider("Positivität", 0, 100, 50)
                
                submitted = st.form_submit_button("Schätzung abgeben")
                if submitted:
                    st.session_state.guesses = {'dance': guess_dance, 'energy': guess_energy, 'valence': guess_valence}
                    st.session_state.guess_submitted = True
                    st.rerun()
        else:
            # --- ERGEBNISSE ANZEIGEN ---
            actual_values = {
                'dance': int(song['danceability'] / 10),
                'energy': int(song['energy'] / 10),
                'valence': int(song['valence'] / 10)
            }
            user_guesses = st.session_state.guesses
            
            round_score = 0
            st.subheader("Auswertung der Runde")
            st.write(f"Der Song war **{song['name']}** von **{song['display_artists']}**.")

            cols = st.columns(3)
            for i, attr in enumerate(['dance', 'energy', 'valence']):
                actual = actual_values[attr]
                guess = user_guesses[attr]
                diff = abs(actual - guess)
                points = max(0, 100 - diff) # 100 Punkte - 1 Punkt Abzug pro % Abweichung
                round_score += points
                
                with cols[i]:
                    st.metric(
                        label=attr.capitalize(),
                        value=f"{actual}%",
                        delta=f"{points} Pkt. (deine Schätzung: {guess}%)",
                        delta_color="off"
                    )
            
            st.session_state.total_score += round_score
            st.success(f"Du hast in dieser Runde {round_score} von 300 möglichen Punkten erreicht!")

            if st.button("Nächster Song"):
                st.session_state.game_round += 1
                st.session_state.guess_submitted = False
                st.session_state.current_song = df_game.sample(1).iloc[0]
                st.rerun()


# --- HAUPTLOGIK ZUR SEITENAUSWAHL ---
if df is None:
    st.stop()

# Initialisiere die aktuelle Seite im Session State
if 'page' not in st.session_state:
    st.session_state.page = 'Explorer'

# Seitenleiste für die Navigation
st.sidebar.title("Navigation")

st.sidebar.markdown("<br>", unsafe_allow_html=True)

if st.sidebar.button("Musik-Explorer", use_container_width=True, type=("primary" if st.session_state.page == 'Explorer' else "secondary")):
    st.session_state.page = 'Explorer'
    st.rerun()

if st.sidebar.button("Song-Quiz", use_container_width=True, type=("primary" if st.session_state.page == 'Game' else "secondary")):
    st.session_state.page = 'Game'
    st.rerun()

# Lade die ausgewählte Seite
if st.session_state.page == 'Explorer':
    explorer_page(df)
elif st.session_state.page == 'Game':
    game_page(df)
