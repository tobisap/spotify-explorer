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

# --- CSS für den Spotify Dark Mode & Mobile Optimierung ---
spotify_dark_mode_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
body, .main { 
    background-color: #121212; 
    font-family: 'Montserrat', sans-serif; 
    color: #FFFFFF; 
}
h1 { 
    color: #1DB954; 
    font-weight: 700; 
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

/* NEU: Mobile Optimierung - Schriftgröße für kleine Bildschirme anpassen */
@media (max-width: 640px) {
    h1 {
        font-size: 2.5rem !important;
    }
    .st-emotion-cache-1b0g02j .st-emotion-cache-1r2n0i { /* Metrik-Wert */
        font-size: 2rem !important;
    }
}
</style>
"""
st.markdown(spotify_dark_mode_css, unsafe_allow_html=True)


# --- Daten laden und bereinigen ---
@st.cache_data
def load_data():
    """Lädt die CSV-Datei und bereinigt die Daten für die App."""
    try:
        df = pd.read_csv('data_vers2.csv')
    except FileNotFoundError:
        st.error("FEHLER: Die Datei 'data_vers2.csv' wurde nicht gefunden.")
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
    st.info("Keine ladbaren Daten in der CSV-Datei gefunden.")
    st.stop()

# --- Seitenleiste mit Filtern (bleibt für alle Tabs gleich) ---
st.sidebar.header("Filter")
filtered_df = df.copy()

if 'decade' in filtered_df.columns:
    decades = sorted(filtered_df['decade'].unique())
    decade_options = [f"{decade}er" for decade in decades]
    start_decade_str, end_decade_str = st.sidebar.select_slider(
        "Jahrzehnt", options=decade_options, 
        value=(decade_options[max(0, len(decade_options)-4)], decade_options[-1])
    )
    start_decade = int(start_decade_str.replace('er', ''))
    end_decade = int(end_decade_str.replace('er', ''))
    filtered_df = filtered_df[(filtered_df['decade'] >= start_decade) & (filtered_df['decade'] <= end_decade)]

# Weitere Filter...
if 'danceability' in filtered_df.columns:
    dance_range = st.sidebar.slider("Tanzbarkeit (0-100)", 0, 100, (0, 100))
    filtered_df = filtered_df[(filtered_df['danceability'] >= dance_range[0]/100.0) & (filtered_df['danceability'] <= dance_range[1]/100.0)]
if 'popularity' in filtered_df.columns:
    val = st.sidebar.slider("Popularität", 0, 100, (0, 100))
    filtered_df = filtered_df[(filtered_df['popularity'] >= val[0]) & (filtered_df['popularity'] <= val[1])]
if 'tempo' in filtered_df.columns:
    min_t, max_t = int(df['tempo'].min()//5*5), int(df['tempo'].max()//5*5)+5
    val = st.sidebar.slider("Tempo (BPM)", min_t, max_t, (min_t, max_t), step=5)
    filtered_df = filtered_df[(filtered_df['tempo'] >= val[0]) & (filtered_df['tempo'] <= val[1])]


# --- Haupt-Ansicht mit Tabs ---
tab1, tab2 = st.tabs(["📊 Explorer", "🔗 Korrelationsanalyse"])

with tab1:
    st.header(f"Trends der {start_decade_str} bis zu den {end_decade_str}")

    if filtered_df.empty:
        st.warning("Keine Songs für die aktuelle Filterkombination gefunden.")
    else:
        # Bereinige Künstlernamen
        if 'artists' in filtered_df.columns:
            filtered_df['display_artists'] = filtered_df['artists'].str.replace(r"\[|\]|'", "", regex=True)
        else:
            filtered_df['display_artists'] = "N/A"

        # Metriken
        col1, col2, col3 = st.columns(3)
        col1.metric("Songs gefunden", f"{len(filtered_df)}")
        col2.metric("Ø Energie", f"{filtered_df['energy'].mean():.2f}")
        col3.metric("Ø Positivität", f"{filtered_df['valence'].mean():.2f}")

        # Diagramm-Steuerung
        with st.expander("Diagramm-Achsen anpassen"):
            axis_options_german = {
                'danceability': 'Tanzbarkeit', 'energy': 'Energie', 'tempo': 'Tempo',
                'popularity': 'Popularität', 'valence': 'Positivität', 'year': 'Jahr'
            }
            col_x, col_y = st.columns(2)
            with col_x:
                x_axis_german = st.selectbox("X-Achse:", options=list(axis_options_german.values()), index=3)
            with col_y:
                y_axis_german = st.selectbox("Y-Achse:", options=list(axis_options_german.values()), index=1)
            x_axis = [key for key, value in axis_options_german.items() if value == x_axis_german][0]
            y_axis = [key for key, value in axis_options_german.items() if value == y_axis_german][0]

        # Diagramm
        st.subheader(f"{x_axis.capitalize()} vs. {y_axis.capitalize()}")
        st.caption("Die Größe und Farbe der Punkte repräsentiert die Popularität des Songs.")
        fig = px.scatter(
            filtered_df, x=x_axis, y=y_axis, color="popularity",
            color_continuous_scale=["#FFFFFF", "#1DB954"],
            size="popularity", size_max=40, hover_name="name"
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#282828", font_color="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)
        
        # Song-Details
        st.subheader("Song-Details anzeigen")
        sorted_songs = filtered_df.sort_values(by='popularity', ascending=False)
        song_list = [""] + sorted_songs['name'].tolist()
        selected_song_name = st.selectbox("Wähle einen Song (sortiert nach Popularität):", options=song_list, label_visibility="collapsed")
        if selected_song_name:
            selected_song = filtered_df[filtered_df['name'] == selected_song_name].iloc[0]
            col_info, col_button = st.columns([3, 1])
            with col_info:
                st.markdown(f"**Titel:** {selected_song['name']}")
                st.markdown(f"**Künstler:** {selected_song['display_artists']}")
            link_col = 'Link' if 'Link' in selected_song and pd.notna(selected_song['Link']) else 't' if 't' in selected_song and pd.notna(selected_song['t']) else None
            if link_col:
                with col_button:
                    st.write("")
                    st.link_button("Auf Spotify öffnen", selected_song[link_col])

with tab2:
    st.header("Korrelationsanalyse der Merkmale")
    st.info("Diese Heatmap zeigt, wie die verschiedenen Song-Eigenschaften für deine aktuelle Auswahl zusammenhängen. Werte nahe 1 (hellgrün) zeigen einen starken positiven Zusammenhang.")
    
    if not filtered_df.empty:
        corr_cols = ['danceability', 'energy', 'tempo', 'popularity', 'valence', 'year']
        corr_df = filtered_df[[col for col in corr_cols if col in filtered_df.columns]]
        matrix = corr_df.corr()
        fig_corr = px.imshow(
            matrix, text_auto=True, aspect="auto",
            color_continuous_scale='Greens', labels={"color": "Korrelation"}
        )
        fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#282828", font_color="#FFFFFF")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("Keine Daten für die Analyse verfügbar. Bitte Filter anpassen.")
