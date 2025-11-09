import requests
import json
import time
import sys, os
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

env_path = Path(__file__).resolve().parent.parent
env_path = env_path / ".env"
print("Loading .env from:", env_path)
                                 
if load_dotenv(env_path):
    # for local development
    API_TOKEN = os.getenv('TMDB_API_TOKEN')
else:
    API_TOKEN = os.environ['TMDB_API_TOKEN']

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}



def get_all_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        genres = response.json().get("genres", [])
        return {g["id"]: g["name"] for g in genres}
    print("Failed to fetch genres:", response.text)
    return {}


def get_movies_by_genre(genre_id, max_pages=1):
    movies = []
    for page in range(1, max_pages + 1):
        url = f"https://api.themoviedb.org/3/discover/movie?with_genres={genre_id}&language=en-US&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch movies for genre ID {genre_id}: {response.text}")
            break
        movies.extend(response.json().get("results", []))
        time.sleep(0.25)
    return movies


def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    for _ in range(3):  # retry 3 times if failed
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        time.sleep(0.5)
    return {}


def get_movie_credits(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    for _ in range(3):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            cast = [c["name"] for c in data.get("cast", [])[:5]]  # top 5 actors
            director = next((c["name"] for c in data.get("crew", []) if c["job"] == "Director"), None)
            return cast, director
        time.sleep(0.5)
    return [], None


def merge_movies_with_credits(genre_map, max_pages=1):
    all_movies = {}
    for genre_id, genre_name in genre_map.items():
        print(f"Fetching movies for genre: {genre_name}")
        movies = get_movies_by_genre(genre_id, max_pages)
        for movie in movies:
            movie_id = movie["id"]
            if movie_id not in all_movies:
                all_movies[movie_id] = {
                    "title": movie.get("title", "N/A"),
                    "genres": [genre_name],
                    "release_date": movie.get("release_date", "N/A"),
                    "rating": movie.get("vote_average", "N/A"),
                    "overview": movie.get("overview", "No description available."),
                }
            elif genre_name not in all_movies[movie_id]["genres"]:
                all_movies[movie_id]["genres"].append(genre_name)

    print("Enriching movies with detailed credits...")
    for movie_id, movie_data in all_movies.items():
        details = get_movie_details(movie_id)
        cast, director = get_movie_credits(movie_id)
        movie_data["actors"] = cast
        movie_data["director"] = director
        movie_data["runtime"] = details.get("runtime", "N/A")
        movie_data["production_companies"] = [p["name"] for p in details.get("production_companies", [])]
        movie_data["popularity"] = details.get("popularity", "N/A")
        print(f"Enriched: {movie_data['title']}")
        time.sleep(0.25)

    return list(all_movies.values())


def main(max_pages):
    print("Starting TMDB movie extraction...")
    print(f"Max pages per genre: {max_pages}")
    #time.sleep(1)  # Simulate startup delay
    #exit()
    # Assume this is the current script path
    script_path = Path(__file__).resolve().parent  # e.g., C:\Users\kjkon\Documents\moviesearch\pages

    # Replace 'pages' with 'data'
    data_path = script_path.with_name("data")
    data_path = data_path / "tmdb_movies_full_credits.json"

    genre_map = get_all_genres()
    all_movies = merge_movies_with_credits(genre_map, max_pages)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_movies, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(all_movies)} movies with full credits to 'tmdb_movies_full_credits.json'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extractmovie.py <max_pages>")
        sys.exit(1)

    max_pages = int(sys.argv[1])
    main(max_pages)
