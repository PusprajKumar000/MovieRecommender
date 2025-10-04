import pickle
import streamlit as st
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retries():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=e67761af91cc5600542ee8f31f55808f&language=en-US"
    
    try:
        session = create_session_with_retries()
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        poster_path = data.get('poster_path')
        
        if poster_path:
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
            return full_path
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster+Available"
            
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch poster for movie ID {movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=Error+Loading+Poster"

def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        recommended_movie_names = []
        recommended_movie_posters = []
        
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].movie_id
            poster_url = fetch_poster(movie_id)
            recommended_movie_posters.append(poster_url)
            recommended_movie_names.append(movies.iloc[i[0]].title)
            
        return recommended_movie_names, recommended_movie_posters
        
    except Exception as e:
        st.error(f"Error in recommendation: {e}")
        return [], []

st.header('Movie Recommender System')

# Load data with error handling
try:
    movies = pickle.load(open('model/movie_list.pkl','rb'))
    similarity = pickle.load(open('model/similarity.pkl','rb'))
except FileNotFoundError:
    st.error("Data files not found. Please make sure 'movie_list.pkl' and 'similarity.pkl' are in the correct directory.")
    st.stop()

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    with st.spinner('Finding recommendations...'):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)
    
    if recommended_movie_names:
        # Use current Streamlit columns syntax (beta_columns is deprecated)
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.text(recommended_movie_names[i])
                st.image(recommended_movie_posters[i])
    else:
        st.error("No recommendations could be generated. Please try again.")