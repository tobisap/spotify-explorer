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
.stLinkButton>a {
    background-color: #1DB954; color: #FFFFFF !important; border-radius: 500px;
    padding: 10px 25px; font-weight: 700; border: none; text-decoration: none;
    display: inline-block; text-align: center;
}
.stLinkButton>a:hover { background-color: #1ED760; color: #FFFFFF !important; }
</style>
"""
st.markdown(spotify_dark_mode_css, unsafe_allow_html=True)


# --- Daten laden und bereinigen ---
@st.cache_data
def load_data():
    """Lädt die CSV-Datei und bereinigt die Daten für die App."""
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

    return df


df = load_data()

# --- Hauptteil der App ---
st.title("Spotify Musik-Explorer")

if df.empty:
    st.info("Keine ladbaren Daten in der CSV-Datei gefunden. Bitte die Datei überprüfen.")
    st.stop()

# --- Seitenleiste mit Filtern ---
st.sidebar.header("Filter")

# GEÄNDERT: Suchfeld-Beschriftung angepasst
search_term = st.sidebar.text_input("Song- oder Künstlersuche", key="song_search")

filtered_df = df.copy()

# GEÄNDERT: Suche nach Song UND Künstler
if search_term:
    # `case=False` ignoriert Groß- und Kleinschreibung. `|` bedeutet ODER.
    filtered_df = filtered_df[
        filtered_df['name'].str.contains(search_term, case=False, na=False) |
        filtered_df['display_artists'].str.contains(search_term, case=False, na=False)
    ]
# Die restlichen Filter werden auf das (möglicherweise schon durch die Suche verkleinerte) Set angewendet
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

if 'danceability' in filtered_df.columns:
    dance_range = st.sidebar.slider("Tanzbarkeit (0-100)", 0, 100, (0, 100), key="dance_slider")
    min_dance = dance_range[0] / 100.0
    max_dance = dance_range[1] / 100.0
    filtered_df = filtered_df[(filtered_df['danceability'] >= min_dance) & (filtered_df['danceability'] <= max_dance)]

if 'popularity' in filtered_df.columns:
    val = st.sidebar.slider("Popularität", 0, 100, (0, 100), key="pop_slider")
    filtered_df = filtered_df[(filtered_df['popularity'] >= val[0]) & (filtered_df['popularity'] <= val[1])]

if 'tempo' in filtered_df.columns:
    min_t = int(df['tempo'].min() // 5 * 5)
    max_t = int(df['tempo'].max() // 5 * 5) + 5
    val = st.sidebar.slider("Tempo (BPM)", min_t, max_t, (min_t, max_t), step=5, key="tempo_slider")
    filtered_df = filtered_df[(filtered_df['tempo'] >= val[0]) & (filtered_df['tempo'] <= val[1])]

# --- Haupt-Ansicht auf der Seite ---
st.header(f"Trends der {start_decade_str} bis zu den {end_decade_str}")

if filtered_df.empty:
    st.warning("Keine Songs für die aktuelle Filterkombination gefunden.")
else:
    # Bereinige die Künstlernamen für eine schönere Anzeige
    if 'artists' in filtered_df.columns:
        filtered_df['display_artists'] = filtered_df['artists'].str.replace(r"\[|\]|'", "", regex=True)
    else:
        filtered_df['display_artists'] = "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Songs gefunden", f"{len(filtered_df)}")
    col2.metric("Ø Energie", f"{filtered_df['energy'].mean():.2f}")
    col3.metric("Ø Positivität", f"{filtered_df['valence'].mean():.2f}")

    # --- Interaktive Auswahl der Achsen-Parameter ---
    st.subheader("Dynamische Analyse")

    # Dictionary für die Anzeige der deutschen Namen in den Dropdowns
    axis_options_german = {
        'danceability': 'Tanzbarkeit',
        'energy': 'Energie',
        'tempo': 'Tempo',
        'popularity': 'Popularität',
        'valence': 'Positivität',
        'year': 'Jahr'
    }

    col_x, col_y = st.columns(2)
    with col_x:
        x_axis_german = st.selectbox("Wähle die X-Achse:", options=list(axis_options_german.values()), index=3)
    with col_y:
        y_axis_german = st.selectbox("Wähle die Y-Achse:", options=list(axis_options_german.values()), index=1)

    # Finde die englischen Originalnamen für die Datenverarbeitung
    x_axis = [key for key, value in axis_options_german.items() if value == x_axis_german][0]
    y_axis = [key for key, value in axis_options_german.items() if value == y_axis_german][0]

    st.subheader(f"{x_axis.capitalize()} vs. {y_axis.capitalize()}")

    fig = px.scatter(
        filtered_df,
        x=x_axis,
        y=y_axis,
        color="popularity",
        color_continuous_scale=["#FFFFFF", "#1DB954"],
        size="popularity",
        size_max=60,
        hover_name="name"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#273126",
        font_color="#FFFFFF",
        hoverlabel=dict(bgcolor="#191414", font_size=16, font_family="Montserrat")
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Korrelationsmatrix in einem ausklappbaren Bereich ---
    with st.expander("Korrelationsmatrix der Merkmale anzeigen"):
        st.write("Diese Heatmap zeigt, wie die verschiedenen Song-Eigenschaften für alle Songs zusammenhängen. Werte nahe 1 (grün) zeigen einen starken positiven Zusammenhang.")
        corr_cols = ['danceability', 'energy', 'tempo', 'popularity', 'valence', 'year']
        corr_df = filtered_df[[col for col in corr_cols if col in filtered_df.columns]]
        
        matrix = corr_df.corr()
        
        # Erstelle die Heatmap mit passender Farbskala
        fig_corr = px.imshow(
            matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='Greens', # GEÄNDERT: Grüne Farbskala
            labels={"color": "Korrelation"}
        )
        fig_corr.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#282828",
            font_color="#FFFFFF"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    
 # --- Song-Auswahl und Player-Anzeige ---
    st.subheader("Song-Details und Player")
    sorted_songs = filtered_df.sort_values(by='popularity', ascending=False)
    
    sorted_songs['display_option'] = sorted_songs['name'] + ' – ' + sorted_songs['display_artists']
    song_list = [""] + sorted_songs['display_option'].tolist()
    
    selected_option = st.selectbox("Wähle einen Song, um ihn abzuspielen:", options=song_list, key="song_select")
    
    if selected_option:
        selected_song = sorted_songs[sorted_songs['display_option'] == selected_option].iloc[0]
        
        # ENTFERNT: Die doppelte Textanzeige wurde hier gelöscht.
        # st.markdown(f"**Titel:** {selected_song['name']} | **Künstler:** {selected_song['display_artists']}")
        
        link_col = 'Link' if 'Link' in selected_song and pd.notna(selected_song['Link']) else 't' if 't' in selected_song and pd.notna(selected_song['t']) else None

        if link_col:
            try:
                track_id = selected_song[link_col].split('/track/')[-1].split('?')[0]
                embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
                
                # Nur noch der Player wird angezeigt
                st.components.v1.iframe(embed_url, height=80)
            except:
                st.warning("Der Spotify-Link für diesen Song scheint ungültig zu sein.")
        else:
            st.warning("Kein Spotify-Link für diesen Song verfügbar.")
