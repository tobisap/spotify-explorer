import streamlit as st
import pandas as pd
import random
import ast
from datetime import datetime

# --- Konfiguration & Design ---
st.set_page_config(
    page_title="Spotify Song-Quiz",
    page_icon="🎯",
    layout="wide"
)

# CSS für den Spotify Dark Mode (gleich wie auf der ersten Seite)
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
    border-bottom: 1px solid #535353;
    padding-bottom: 3rem;
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
.quiz-container {
    background-color: #282828;
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem 0;
    border: 2px solid #1DB954;
}
.score-display {
    background-color: #1DB954;
    color: #FFFFFF;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    font-weight: 700;
    font-size: 1.2em;
}
.highscore-table {
    background-color: #282828;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
"""
st.markdown(spotify_dark_mode_css, unsafe_allow_html=True)

# --- Daten laden ---
@st.cache_data
def load_data():
    """Lädt die Datei und bereinigt die Daten für die App."""
    df = pd.DataFrame()
    
    # Versuche verschiedene Dateiformate zu laden
    file_options = [
        ('data_final.parquet', 'parquet'),
        ('data_final.csv', 'csv'),
        ('spotify_data.csv', 'csv'),
        ('spotify_data.parquet', 'parquet')
    ]
    
    for filename, file_type in file_options:
        try:
            if file_type == 'parquet':
                df = pd.read_parquet(filename)
                st.success(f"✅ Daten erfolgreich geladen aus: {filename}")
                break
            elif file_type == 'csv':
                df = pd.read_csv(filename)
                st.success(f"✅ Daten erfolgreich geladen aus: {filename}")
                break
        except FileNotFoundError:
            continue
        except Exception as e:
            st.warning(f"⚠️ Fehler beim Laden von {filename}: {str(e)}")
            continue
    
    if df.empty:
        st.error("❌ FEHLER: Keine gültige Datendatei gefunden. Bitte stellen Sie sicher, dass eine der folgenden Dateien vorhanden ist:")
        for filename, _ in file_options:
            st.write(f"- {filename}")
        return pd.DataFrame()
    
    # Datenbereinigung
    numeric_cols = ['year', 'danceability', 'popularity', 'tempo', 'energy', 'valence']
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    if not available_cols:
        st.error("❌ FEHLER: Keine der erforderlichen Spalten gefunden!")
        st.write("Erforderliche Spalten:", numeric_cols)
        st.write("Verfügbare Spalten:", list(df.columns))
        return pd.DataFrame()
    
    # Konvertiere numerische Spalten
    for col in available_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Entferne Zeilen mit fehlenden Werten in wichtigen Spalten
    essential_cols = ['danceability', 'energy', 'valence', 'popularity']
    essential_available = [col for col in essential_cols if col in df.columns]
    
    if essential_available:
        df.dropna(subset=essential_available, inplace=True)
    
    if 'year' in df.columns:
        df['year'] = df['year'].astype(int, errors='ignore')
    
    # Bereite Künstler-Anzeige vor
    if 'artists' in df.columns:
        df['display_artists'] = df['artists'].astype(str).str.replace(r"\[|\]|'", "", regex=True)
    elif 'artist' in df.columns:
        df['display_artists'] = df['artist'].astype(str)
    else:
        df['display_artists'] = "Unbekannter Künstler"
    
    # Stelle sicher, dass wir einen Song-Namen haben
    if 'name' not in df.columns:
        if 'title' in df.columns:
            df['name'] = df['title']
        elif 'song' in df.columns:
            df['name'] = df['song']
        else:
            df['name'] = "Unbekannter Song"
    
    st.info(f"📊 {len(df)} Songs geladen mit {len(df.columns)} Attributen")
    
    return df

# --- Highscore-Funktionen ---
def load_highscores():
    """Lädt die Highscores aus der Session State."""
    if 'highscores' not in st.session_state:
        st.session_state.highscores = []
    return st.session_state.highscores

def save_highscore(name, score):
    """Speichert einen neuen Highscore."""
    if 'highscores' not in st.session_state:
        st.session_state.highscores = []
    
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    st.session_state.highscores.append({
        'name': name,
        'score': score,
        'date': timestamp
    })
    
    # Sortiere nach Score (absteigend) und behalte nur die Top 5
    st.session_state.highscores = sorted(st.session_state.highscores, key=lambda x: x['score'], reverse=True)[:5]

def display_highscores():
    """Zeigt die Highscore-Tabelle an."""
    highscores = load_highscores()
    
    if highscores:
        st.markdown('<div class="highscore-table">', unsafe_allow_html=True)
        st.subheader("🏆 Top 5 Highscores")
        
        for i, entry in enumerate(highscores, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            st.markdown(f"**{medal} {entry['name']}** - {entry['score']} Punkte _{entry['date']}_")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Noch keine Highscores vorhanden. Sei der Erste!")

# --- Spiel-Logik ---
def calculate_score(guess, actual):
    """Berechnet die Punkte basierend auf der Genauigkeit der Schätzung."""
    # Wandle beide Werte in 0-100 Skala um
    if isinstance(actual, float) and actual <= 1:
        actual = actual * 100
    if isinstance(guess, float) and guess <= 1:
        guess = guess * 100
    
    # Berechne den Unterschied
    diff = abs(guess - actual)
    
    # Punktesystem: 100 Punkte für perfekte Schätzung, linear abnehmend
    score = max(0, 100 - diff)
    return int(score)

def initialize_game():
    """Initialisiert ein neues Spiel."""
    st.session_state.current_song = 0
    st.session_state.total_score = 0
    st.session_state.game_songs = []
    st.session_state.game_active = True
    st.session_state.show_result = False
    st.session_state.song_scores = []

def get_random_song(df):
    """Wählt einen zufälligen Song aus."""
    # Prüfe verfügbare Link-Spalten
    link_columns = []
    for col in ['Link', 'link', 'spotify_url', 'url', 't']:
        if col in df.columns:
            link_columns.append(col)
    
    # Versuche Songs mit Links zu finden
    songs_with_links = df.copy()
    if link_columns:
        # Filtere Songs die mindestens einen Link haben
        mask = pd.Series(False, index=df.index)
        for col in link_columns:
            mask = mask | df[col].notna()
        songs_with_links = df[mask]
    
    # Wähle aus Songs mit Links, falls vorhanden, sonst alle Songs
    if len(songs_with_links) > 0:
        return songs_with_links.sample(1).iloc[0]
    else:
        return df.sample(1).iloc[0]

# --- Hauptteil der App ---
st.title("🎯 Spotify Song-Quiz")

df = load_data()

if df.empty:
    st.info("Keine ladbaren Daten in der CSV-Datei gefunden. Bitte die Datei überprüfen.")
    st.stop()

# Spiel-Zustand initialisieren
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
    st.session_state.current_song = 0
    st.session_state.total_score = 0
    st.session_state.game_songs = []
    st.session_state.show_result = False
    st.session_state.song_scores = []

# Spielerklärung
st.markdown("""
### 🎮 Wie funktioniert das Spiel?

1. **5 Songs** werden zufällig aus der Datenbank ausgewählt
2. Für jeden Song schätzt du die **Attribute** (Tanzbarkeit, Energie, Positivität, Popularität)
3. Je genauer deine Schätzung, desto mehr **Punkte** bekommst du (max. 100 pro Attribut)
4. Am Ende kannst du deinen **Highscore** speichern und dich mit anderen messen!
""")

# Start/Restart Button
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🎵 Neues Spiel starten", type="primary"):
        initialize_game()
        # Wähle 5 zufällige Songs
        st.session_state.game_songs = [get_random_song(df) for _ in range(5)]

# Spiel-Interface
if st.session_state.game_active and st.session_state.game_songs:
    current_song_index = st.session_state.current_song
    
    if current_song_index < len(st.session_state.game_songs):
        song = st.session_state.game_songs[current_song_index]
        
        # Fortschrittsanzeige
        progress = (current_song_index) / 5
        st.progress(progress)
        st.markdown(f"**Song {current_song_index + 1} von 5**")
        
        # Song-Anzeige
        st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
        st.subheader(f"🎵 {song['name']}")
        st.markdown(f"**Künstler:** {song['display_artists']}")
        
        # Spotify Player
        link_columns = ['Link', 'link', 'spotify_url', 'url', 't']
        link_col = None
        
        for col in link_columns:
            if col in song and pd.notna(song[col]) and str(song[col]) != 'nan':
                link_col = col
                break
        
        if link_col:
            try:
                link_url = str(song[link_col])
                if '/track/' in link_url:
                    track_id = link_url.split('/track/')[-1].split('?')[0]
                    embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0"
                    st.components.v1.iframe(embed_url, height=152)
                else:
                    st.warning("⚠️ Ungültiger Spotify-Link Format.")
            except Exception as e:
                st.warning(f"⚠️ Spotify-Player nicht verfügbar: {str(e)}")
        else:
            st.info("ℹ️ Kein Spotify-Link für diesen Song verfügbar.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Schätzungen
        st.subheader("📊 Schätze die Song-Attribute:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            guess_dance = st.slider("🕺 Tanzbarkeit (0-100)", 0, 100, 50, key=f"dance_{current_song_index}")
            guess_energy = st.slider("⚡ Energie (0-100)", 0, 100, 50, key=f"energy_{current_song_index}")
        
        with col2:
            guess_valence = st.slider("😊 Positivität (0-100)", 0, 100, 50, key=f"valence_{current_song_index}")
            guess_popularity = st.slider("📈 Popularität (0-100)", 0, 100, 50, key=f"pop_{current_song_index}")
        
        # Bestätigen Button
        if st.button("✅ Schätzung bestätigen", key=f"confirm_{current_song_index}"):
            # Sichere Attribut-Extraktion
            actual_dance = song.get('danceability', 0.5)
            actual_energy = song.get('energy', 0.5)
            actual_valence = song.get('valence', 0.5)
            actual_popularity = song.get('popularity', 50)
            
            # Normalisiere Werte auf 0-100 Skala
            if actual_dance <= 1:
                actual_dance = actual_dance * 100
            if actual_energy <= 1:
                actual_energy = actual_energy * 100
            if actual_valence <= 1:
                actual_valence = actual_valence * 100
            
            # Berechne Punkte
            score_dance = calculate_score(guess_dance, actual_dance)
            score_energy = calculate_score(guess_energy, actual_energy)
            score_valence = calculate_score(guess_valence, actual_valence)
            score_popularity = calculate_score(guess_popularity, actual_popularity)
            
            song_total = score_dance + score_energy + score_valence + score_popularity
            
            # Speichere Ergebnis
            st.session_state.song_scores.append({
                'song': song.get('name', 'Unbekannter Song'),
                'artist': song.get('display_artists', 'Unbekannter Künstler'),
                'scores': {
                    'Tanzbarkeit': score_dance,
                    'Energie': score_energy,
                    'Positivität': score_valence,
                    'Popularität': score_popularity
                },
                'total': song_total,
                'actual': {
                    'Tanzbarkeit': actual_dance,
                    'Energie': actual_energy,
                    'Positivität': actual_valence,
                    'Popularität': actual_popularity
                },
                'guessed': {
                    'Tanzbarkeit': guess_dance,
                    'Energie': guess_energy,
                    'Positivität': guess_valence,
                    'Popularität': guess_popularity
                }
            })
            
            st.session_state.total_score += song_total
            st.session_state.current_song += 1
            
            if st.session_state.current_song >= 5:
                st.session_state.game_active = False
                st.session_state.show_result = True
            
            st.rerun()

# Ergebnis anzeigen
if st.session_state.show_result and st.session_state.song_scores:
    st.markdown('<div class="score-display">', unsafe_allow_html=True)
    st.subheader("🎉 Spiel beendet!")
    st.markdown(f"**Gesamtpunktzahl: {st.session_state.total_score} / 2000**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detaillierte Ergebnisse
    st.subheader("📋 Detaillierte Ergebnisse:")
    
    for i, result in enumerate(st.session_state.song_scores, 1):
        with st.expander(f"Song {i}: {result['song']} - {result['artist']} ({result['total']} Punkte)"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Deine Schätzung:**")
                for attr, guess in result['guessed'].items():
                    st.write(f"{attr}: {guess:.0f}")
            
            with col2:
                st.markdown("**Tatsächliche Werte:**")
                for attr, actual in result['actual'].items():
                    st.write(f"{attr}: {actual:.0f}")
            
            with col3:
                st.markdown("**Punkte:**")
                for attr, score in result['scores'].items():
                    st.write(f"{attr}: {score}")
    
    # Highscore speichern
    st.subheader("💾 Highscore speichern:")
    player_name = st.text_input("Dein Name:", max_chars=20)
    
    if st.button("🏆 Highscore speichern") and player_name:
        save_highscore(player_name, st.session_state.total_score)
        st.success(f"Highscore gespeichert! {player_name}: {st.session_state.total_score} Punkte")
        st.rerun()

# Highscore-Tabelle anzeigen
st.markdown("---")
display_highscores()

# Reset-Button für Admin
if st.button("🔄 Highscores zurücksetzen", help="Achtung: Löscht alle gespeicherten Highscores!"):
    st.session_state.highscores = []
    st.success("Highscores wurden zurückgesetzt!")
    st.rerun()
