import re
import json
from pathlib import Path
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

import os

metadatas_global = []

env_path = Path(__file__).resolve().parent.parent
env_path = env_path / ".env"
print("Loading .env from:", env_path)
                                 
# Pass the API Key to the OpenAI Client
if load_dotenv(env_path):
   # for local development
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
else:
   client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

class MovieSearchAgent:
    def __init__(self, db_dir=None, collection_name="movies_rag", model_name="all-MiniLM-L6-v2"):
        # --- Setup paths ---
        script_path = Path(__file__).resolve().parent
        index_path = script_path.with_name("data")
        self.index_path = index_path
        self.chroma_db_dir = db_dir or (index_path / "chroma_db")

        # --- Connect to Chroma DB ---
        self.chroma_client = PersistentClient(path=self.chroma_db_dir)
        self.collection = self.chroma_client.get_collection(name=collection_name)

        # --- Load embedding model once ---
        self.model = SentenceTransformer(model_name)

        # --- Load indexes ---
        self.indexes = {
            "actor": self._load_index("actor"),
            "director": self._load_index("director"),
            "genre": self._load_index("genre"),
            "company": self._load_index("company"),
            "year": self._load_index("year"),
        }

    def _load_index(self, index_name):
        path = self.index_path / f"{index_name}_index.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"⚠️ Index '{index_name}' not found at {path}")
            return {}

    def _is_clause_structured(self, clause):
        clause = clause.strip().lower()
        patterns = [
            r"(acted by|starring|featuring)\s+(.+)",
            r"(directed by|by director)\s+(.+)",
            r"(produced by|production|distributed by)\s+(.+)",
            r"(genre is|genre in|type is)\s+(.+)",
            r"(after|before|in)\s+(\d{4})"
        ]
        return any(re.search(p, clause) for p in patterns)

    def _filter_clause(self, clause):
        clause = clause.strip().lower()

        if m := re.search(r"(acted by|starring|featuring)\s+(.+)", clause):
            return self.indexes["actor"].get(m.group(2).strip(), [])

        if m := re.search(r"(directed by|by director)\s+(.+)", clause):
            return self.indexes["director"].get(m.group(2).strip(), [])

        if m := re.search(r"(produced by|production|distributed by)\s+(.+)", clause):
            return self.indexes["company"].get(m.group(2).strip(), [])

        if m := re.search(r"(genre is|genre in|type is)\s+(.+)", clause):
            return self.indexes["genre"].get(m.group(2).strip(), [])

        if m := re.search(r"(after|before|in)\s+(\d{4})", clause):
            relation, year = m.groups()
            year = int(year)
            results = []
            for y, movies in self.indexes["year"].items():
                try:
                    y_int = int(y)
                    if (relation == "after" and y_int > year) or \
                       (relation == "before" and y_int < year) or \
                       (relation == "in" and y_int == year):
                        results.extend(movies)
                except ValueError:
                    continue
            return results

        return []

    def search(self, query, n_results=5):
        clauses = [c.strip() for c in query.lower().split(" and ") if c.strip()]
        if not clauses:
            print("⚠️ No valid clauses found in query.")
            return []

        semantic_sets = []
        structured_sets = []

        for clause in clauses:
            if self._is_clause_structured(clause):
                print(f"⏭️ Structured clause detected: '{clause}' — will use index if no semantic clauses")
                matches = self._filter_clause(clause)
                if not matches:
                    print(f"❌ Structured clause '{clause}' returned no results — aborting structured fallback.")
                    return []
                structured_sets.append(set(json.dumps(m) for m in matches))
            else:
                print(f"🧠 Semantic search for unrecognized clause: '{clause}'")
                embedding = self.model.encode(clause).tolist()
                sem_results = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=5,
                    include=["metadatas"]
                )
                print("sem-results:",sem_results)
                metas = sem_results.get("metadatas", [[]])[0]
                if not metas:
                    print(f"❌ Semantic search for '{clause}' returned no results — aborting AND search.")
                    return []
                semantic_sets.append(set(json.dumps(m) for m in metas))

        if semantic_sets:
            final_set = set.intersection(*semantic_sets)
            print("final_set:",final_set)
            if not final_set:
                print("⚠️ No movies matched all semantic conditions.")
                return []
            final_results = [json.loads(m) for m in final_set]
            print(f"\n✅ Found {len(final_results)} movie(s) matching semantic-only clauses:\n")
            for i, m in enumerate(final_results[:n_results], 1):
                print(f"{i}. {m.get('title')} ({m.get('release_date')}) — {m.get('genres')}")
            return final_results

        print("🔁 No unrecognized clauses — using structured index filtering")
        final_set = set.intersection(*structured_sets)
        if not final_set:
            print("⚠️ No movies matched all structured conditions.")
            return []

        final_results = [json.loads(m) for m in final_set]
        print(f"\n✅ Found {len(final_results)} movie(s) matching structured clauses:\n")
        for i, m in enumerate(final_results[:n_results], 1):
            print(f"{i}. {m.get('title')} ({m.get('release_date')}) — {m.get('genres')}")
        return final_results


class MovieRecommenderAgent:
    def __init__(self, model="mistral", host="http://localhost:11434"):
        self.model = model
        self.endpoint = f"{host}/api/generate"

    def _build_prompt(self, user_query, movie_data):
        print(movie_data)
        return f"""
You are a movie expert helping a user find the best movie based on their query.

User query: "{user_query}"

Here are some candidate movies:
{movie_data}

Respond with **only valid JSON**. The title and reason can repeat for multiple movie recommendations.  You can use all the info provided to you such as release_date, director, rating to do the recommendations. Do not use your own recommendation if the movie data does not match the query.  If there is no match, say no match. Use this exact format:

{{
  "recommendations": [
    {{
      "title": "Movie Title",
      "reason": "Why this movie fits the query and briefly describe the plot."
    }},
    ...
  ]
}}
"""

    def _format_movies_for_prompt(self, metadatas):
        print("metadatas:",metadatas)
        
        import agent
        #agent.metadatas_global


        #global metadatas_global
        agent.metadatas_global = metadatas
        print("metadatas_global1:", agent.metadatas_global)
        if not metadatas:
            return "No movies found."

        lines = []
        for i, m in enumerate(metadatas, 1):
            title = m.get("title", "Unknown Title")
            release_date = m.get("release_date", "Unknown Date")
            genres = m.get("genres", "Unknown Genre")
            overview = m.get("overview", "")
            director = m.get("director", "Unknown Director")
            actors = m.get("actors", "Unknown Cast")
            rating = m.get("rating", "Unrated")

            lines.append(
                f"{i}. Title: {title}\n"
                f"   🎬 Release: {release_date}\n"
                f"   🎬 Genres: {genres}\n"
                f"   🎬 Director: {director}\n"
                f"   🎭 Cast: {actors}\n"
                f"   ⭐ Rating: {rating}\n"
                f"   📝 Overview: {overview}"
            )

        return "\n\n".join(lines)

    def recommend(self, user_query, metadatas, max_tokens=1024, temperature=0.7):
        movie_data = self._format_movies_for_prompt(metadatas)
        print("moviedata:", movie_data)
        prompt = self._build_prompt(user_query, movie_data)

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature,
                top_p=1.0,
                max_tokens=max_tokens,
                n=1,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")

        content = response.choices[0].message.content.strip()
        print("LLM response content:", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

class MovieOrchestrator:
    def __init__(self, search_agent: MovieSearchAgent, recommender_agent: MovieRecommenderAgent):
        self.search_agent = search_agent
        self.recommender_agent = recommender_agent

    def run(self, query, n_results=5):
        print(f"\n🔍 Running search agent for query: '{query}'")
        candidates = self.search_agent.search(query, n_results=n_results)
        candidates = candidates[:5]  # ✅ enforce top-5 only
        #print(candidates)
        if not candidates:
            print("⚠️ No candidates found — skipping recommendation.")
            return []

        print("\n🧠 Running recommender agent...\n")
        recommendation = self.recommender_agent.recommend(query, candidates)
        return recommendation


class MovieSearchAgent:
    def __init__(self, db_dir=None, collection_name="movies_rag", model_name="all-MiniLM-L6-v2"):
        # --- Setup paths ---
        script_path = Path(__file__).resolve().parent
        index_path = script_path.with_name("data")
        self.index_path = index_path
        self.chroma_db_dir = db_dir or (index_path / "chroma_db")

        # --- Connect to Chroma DB ---
        self.chroma_client = PersistentClient(path=self.chroma_db_dir)
        self.collection = self.chroma_client.get_collection(name=collection_name)

        # --- Load embedding model once ---
        self.model = SentenceTransformer(model_name)

        # --- Load indexes ---
        self.indexes = {
            "actor": self._load_index("actor"),
            "director": self._load_index("director"),
            "genre": self._load_index("genre"),
            "company": self._load_index("company"),
            "year": self._load_index("year"),
        }

    def _load_index(self, index_name):
        path = self.index_path / f"{index_name}_index.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"⚠️ Index '{index_name}' not found at {path}")
            return {}

    def _is_clause_structured(self, clause):
        clause = clause.strip().lower()
        patterns = [
            r"(acted by|starring|featuring)\s+(.+)",
            r"(directed by|by director)\s+(.+)",
            r"(produced by|production|distributed by)\s+(.+)",
            r"(genre is|genre in|type is)\s+(.+)",
            r"(after|before|in)\s+(\d{4})"
        ]
        return any(re.search(p, clause) for p in patterns)

    def _filter_clause(self, clause):
        clause = clause.strip().lower()

        if m := re.search(r"(acted by|starring|featuring)\s+(.+)", clause):
            return self.indexes["actor"].get(m.group(2).strip(), [])

        if m := re.search(r"(directed by|by director)\s+(.+)", clause):
            return self.indexes["director"].get(m.group(2).strip(), [])

        if m := re.search(r"(produced by|production|distributed by)\s+(.+)", clause):
            return self.indexes["company"].get(m.group(2).strip(), [])

        if m := re.search(r"(genre is|genre in|type is)\s+(.+)", clause):
            return self.indexes["genre"].get(m.group(2).strip(), [])

        if m := re.search(r"(after|before|in)\s+(\d{4})", clause):
            relation, year = m.groups()
            year = int(year)
            results = []
            for y, movies in self.indexes["year"].items():
                try:
                    y_int = int(y)
                    if (relation == "after" and y_int > year) or \
                       (relation == "before" and y_int < year) or \
                       (relation == "in" and y_int == year):
                        results.extend(movies)
                except ValueError:
                    continue
            return results

        return []

    def search(self, query, n_results=5):
        clauses = [c.strip() for c in query.lower().split(" and ") if c.strip()]
        if not clauses:
            print("⚠️ No valid clauses found in query.")
            return []

        semantic_sets = []
        structured_sets = []

        for clause in clauses:
            if self._is_clause_structured(clause):
                print(f"⏭️ Structured clause detected: '{clause}' — will use index if no semantic clauses")
                matches = self._filter_clause(clause)
                if not matches:
                    print(f"❌ Structured clause '{clause}' returned no results — aborting structured fallback.")
                    return []
                structured_sets.append(set(json.dumps(m) for m in matches))
            else:
                print(f"🧠 Semantic search for unrecognized clause: '{clause}'")
                embedding = self.model.encode(clause).tolist()
                sem_results = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=5,
                    include=["metadatas"]
                )
                metas = sem_results.get("metadatas", [[]])[0]
                if not metas:
                    print(f"❌ Semantic search for '{clause}' returned no results — aborting AND search.")
                    return []
                semantic_sets.append(set(json.dumps(m) for m in metas))

        if semantic_sets:
            final_set = set.intersection(*semantic_sets)
            if not final_set:
                print("⚠️ No movies matched all semantic conditions.")
                return []
            final_results = [json.loads(m) for m in final_set]
            print(f"\n✅ Found {len(final_results)} movie(s) matching semantic-only clauses:\n")
            for i, m in enumerate(final_results[:n_results], 1):
                print(f"{i}. {m.get('title')} ({m.get('release_date')}) — {m.get('genres')}")
            return final_results

        print("🔁 No unrecognized clauses — using structured index filtering")
        final_set = set.intersection(*structured_sets)
        if not final_set:
            print("⚠️ No movies matched all structured conditions.")
            return []

        final_results = [json.loads(m) for m in final_set]
        print(f"\n✅ Found {len(final_results)} movie(s) matching structured clauses:\n")
        for i, m in enumerate(final_results[:n_results], 1):
            print(f"{i}. {m.get('title')} ({m.get('release_date')}) — {m.get('genres')}")
        return final_results

def normalize_title(t):
    return str(t or "").strip().lower()

def loose_match(a, b):
    a_norm = normalize_title(a)
    b_norm = normalize_title(b)
    return (
        a_norm in b_norm or
        b_norm in a_norm or
        any(token in b_norm for token in a_norm.split()) or
        any(token in a_norm for token in b_norm.split())
    )

def parse_json_recommendations(response_text):
    try:
        if isinstance(response_text, str):
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[len("```json"):].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            parsed = json.loads(cleaned)
        elif isinstance(response_text, dict):
            parsed = response_text
        else:
            raise ValueError(f"Unsupported response format: {type(response_text)}")

        # Handle case where parsed is a list directly
        if isinstance(parsed, list):
            recommendations = parsed
        elif isinstance(parsed, dict):
            recommendations = parsed.get("recommendations", [])
        else:
            raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

        enriched = []
        import agent
        #global metadatas_global
        print("agent.metadatas_global:", agent.metadatas_global)

        for rec in recommendations:
            if not isinstance(rec, dict):
                continue

            title = str(rec.get("title", "")).strip()
            reason = str(rec.get("reason", "")).strip()

            match = next(
                (m for m in agent.metadatas_global if str(m.get("title", "")).strip().lower() in title.lower()),
                None
            )

            enriched.append({
                "title": title,
                "reason": reason,
                "release_date": match.get("release_date", "") if match else "",
                "director": match.get("director", "") if match else "",
                "actors": match.get("actors", "") if match else "",
                "rating": match.get("rating", "") if match else "",
                "genres": match.get("genres", "") if match else "",
                "overview": match.get("overview", "") if match else "",
                "runtime": match.get("runtime", "") if match else "",
                "popularity": match.get("popularity", "") if match else "",
                "production_companies": match.get("production_companies", "") if match else ""
            })

        print(enriched)
        return enriched

    except Exception as e:
        print("❌ Failed to parse recommendations:", e)
        return []


class MovieOfferAgent:
    def __init__(self, serpapi_key, country="United States"):
        self.api_key = serpapi_key
        self.country = country

    def _extract_prices_and_format(self, snippet):
        rent_price = ""
        buy_price = ""
        format_type = ""

        if not snippet:
            return rent_price, buy_price, format_type

        rent_match = re.search(r"(\$\d+(\.\d{1,2})?)\s*rent", snippet, re.IGNORECASE)
        buy_match = re.search(r"(\$\d+(\.\d{1,2})?)\s*buy", snippet, re.IGNORECASE)
        rent_price = rent_match.group(1) if rent_match else ""
        buy_price = buy_match.group(1) if buy_match else ""

        all_prices = re.findall(r"\$\d+(\.\d{1,2})?", snippet)
        if not rent_price and len(all_prices) >= 1:
            rent_price = all_prices[0]
        if not buy_price and len(all_prices) >= 2:
            buy_price = all_prices[1]

        if re.search(r"\bstream|digital\b", snippet, re.IGNORECASE):
            format_type = "Streaming"
        elif re.search(r"\bDVD\b", snippet, re.IGNORECASE):
            format_type = "DVD"
        elif re.search(r"\bBlu[- ]?ray\b", snippet, re.IGNORECASE):
            format_type = "Blu-ray"
        else:
            format_type = "Unknown"

        return rent_price, buy_price, format_type

    def _detect_platform(self, title, snippet):
        platforms = ["Netflix", "Amazon", "Apple TV", "Google Play", "Disney+", "HBO Max", "YouTube"]
        combined = (title or "") + " " + (snippet or "")
        for p in platforms:
            if p.lower() in combined.lower():
                return p
        if "amazon.com" in (snippet or "").lower() or "amazon.com" in (title or "").lower():
            return "Amazon"
        return ""  # Return empty string when platform not found

    def search_offers(self, movie_title):
        cleaned_title = re.sub(r"\s*\(\d{4}(-\d{2}){0,2}\)", "", movie_title).strip()
        query = f"buy rent stream {cleaned_title} movie site:justwatch.com OR site:amazon.com OR site:apple.com OR site:google.com/movies"
        print(query)

        params = {
            "engine": "google",
            "q": query,
            "location": self.country,
            "api_key": self.api_key,
            "num": 10
        }
        url = "https://serpapi.com/search"
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ SerpAPI request failed: {response.status_code}")
            return []

        data = response.json()
        results = data.get("organic_results", [])

        # Don’t print failure — just try to extract offers anyway
        if not results:
            return []

        offers = []
        for idx, r in enumerate(results, start=1):
            snippet = r.get("snippet", "") or ""
            rent_price, buy_price, format_type = self._extract_prices_and_format(snippet)
            platform = self._detect_platform(r.get("title", "") or "", snippet)

            if not platform:
                continue

            costs = ", ".join(filter(None, [rent_price, buy_price]))

            offers.append({
                "#": idx,
                "Title": r.get("title", ""),
                "Platform": platform,
                "Format": format_type,
                "Rent": rent_price,
                "Buy": buy_price,
                "Costs": costs,
                "URL": r.get("link", "")
            })

            print(f"- {platform} | {format_type} | Rent: {rent_price} | Buy: {buy_price} | {r.get('link', '')}")
        
        return offers


# --- The rest of your script is left unchanged except for printing offers in table form ---
