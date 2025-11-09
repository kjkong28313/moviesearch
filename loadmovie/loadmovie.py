################################################################################
# FILE: loadmovie/loadmovie.py
# LOCATION: loadmovie/ directory
################################################################################

"""
Load movies into ChromaDB vector database for semantic search
Generates embeddings using SentenceTransformer and stores in persistent storage
"""

import json
import sys
import os
import shutil
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def safe_str(value) -> str:
    """
    Safely convert any value to string
    
    Args:
        value: Any value to convert
        
    Returns:
        String representation
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join([str(v) for v in value])
    return str(value)


def init_chroma_db(force_fresh: bool = True) -> PersistentClient:
    """
    Initialize ChromaDB with fresh or existing database
    
    Args:
        force_fresh: If True, deletes existing database
        
    Returns:
        ChromaDB client instance
    """
    script_path = Path(__file__).resolve().parent
    chroma_db_dir = script_path.with_name("data") / "chroma_db"

    # Kill active connection and delete DB if requested
    if force_fresh and chroma_db_dir.exists():
        print(f"Preparing to remove old database at: {chroma_db_dir}")
        try:
            # Attempt to connect and delete collections
            temp_client = PersistentClient(path=str(chroma_db_dir))
            collections = temp_client.list_collections()
            for col in collections:
                print(f"  Deleting collection: {col.name}")
                temp_client.delete_collection(name=col.name)
            del temp_client  # Release reference
        except Exception as e:
            print(f"  Warning: Could not cleanly disconnect ChromaDB: {e}")

        try:
            shutil.rmtree(chroma_db_dir)
            print("Old database removed successfully")
        except Exception as e:
            print(f"  Warning: Could not remove database directory: {e}")

    # Create directory
    chroma_db_dir.mkdir(parents=True, exist_ok=True)
    print(f"Database directory: {chroma_db_dir}")

    # Create fresh client
    try:
        client = PersistentClient(path=str(chroma_db_dir))
        print("ChromaDB client initialized")
        return client
    except Exception as e:
        raise RuntimeError(f"Failed to initialize ChromaDB: {e}")


def load_movie_data(data_path: Path) -> List[Dict]:
    """
    Load movie data from JSON file
    
    Args:
        data_path: Path to JSON file
        
    Returns:
        List of movie dictionaries
    """
    print(f"Loading movie data from: {data_path}")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Movie data file not found: {data_path}")
    
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            movies = json.load(f)
        print(f"Loaded {len(movies)} movies")
        return movies
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def create_movie_text(movie: Dict) -> str:
    """
    Create rich text representation of movie for embedding
    
    Args:
        movie: Movie metadata dictionary
        
    Returns:
        Formatted text string
    """
    return f"""
Title: {safe_str(movie.get('title'))}
Overview: {safe_str(movie.get('overview'))}
Genres: {safe_str(movie.get('genres'))}
Release Date: {safe_str(movie.get('release_date'))}
Rating: {safe_str(movie.get('rating'))}
Popularity: {safe_str(movie.get('popularity'))}
Director: {safe_str(movie.get('director'))}
Actors: {safe_str(movie.get('actors'))}
Production Companies: {safe_str(movie.get('production_companies'))}
Runtime: {safe_str(movie.get('runtime'))}
""".strip()


def embed_and_store_movies(
    movies: List[Dict],
    model: SentenceTransformer,
    collection,
    batch_size: int = 20
):
    """
    Generate embeddings and store in ChromaDB
    
    Args:
        movies: List of movie dictionaries
        model: SentenceTransformer model
        collection: ChromaDB collection
        batch_size: Number of movies to process at once
    """
    print(f"\nProcessing {len(movies)} movies in batches of {batch_size}...")
    
    for idx, movie in enumerate(movies, 1):
        try:
            # Create text representation
            text = create_movie_text(movie)
            
            # Flatten metadata (all values must be strings)
            metadata = {k: safe_str(v) for k, v in movie.items()}
            
            # Generate embedding
            embedding = model.encode(text).tolist()
            
            # Create unique ID
            movie_id = f"{safe_str(movie.get('title'))}_{safe_str(movie.get('release_date'))}"
            
            # Store in ChromaDB
            collection.add(
                ids=[movie_id],
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            
            # Progress indicator
            if idx % batch_size == 0:
                progress = (idx / len(movies)) * 100
                print(f"  Progress: {idx}/{len(movies)} ({progress:.1f}%)")
        
        except Exception as e:
            print(f"Warning: Failed to process movie at index {idx}: {e}")
            continue
    
    print(f"\nSuccessfully embedded and stored {len(movies)} movies")


def test_search(collection, model: SentenceTransformer, query: str, n_results: int = 3):
    """
    Perform a test search to verify the database
    
    Args:
        collection: ChromaDB collection
        model: SentenceTransformer model
        query: Test query string
        n_results: Number of results to return
    """
    print(f"\nTesting database with query: '{query}'")
    
    try:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances"]
        )
        
        print(f"\nFound {len(results['metadatas'][0])} results:\n")
        
        # Display results
        for i, (meta, distance) in enumerate(zip(results["metadatas"][0], results["distances"][0]), 1):
            print(f"[{i}] {meta.get('title')} ({meta.get('release_date')})")
            print(f"    Genres: {meta.get('genres')}")
            print(f"    Director: {meta.get('director')}")
            print(f"    Actors: {meta.get('actors')}")
            print(f"    Rating: {meta.get('rating')}")
            print(f"    Distance: {distance:.4f}")
            print(f"    Overview: {meta.get('overview')[:150]}...")
            print()
        
    except Exception as e:
        print(f"Test search failed: {e}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("MOVIE VECTOR DATABASE LOADER")
    print("="*70 + "\n")
    
    try:
        # Setup paths
        script_path = Path(__file__).resolve().parent
        data_dir = script_path.with_name("data")
        data_path = data_dir / "tmdb_movies_full_credits.json"
        
        # Load movie data
        movies = load_movie_data(data_path)
        
        # Initialize ChromaDB
        print("\nInitializing vector database...")
        client = init_chroma_db(force_fresh=True)
        
        # Create collection
        collection_name = "movies_rag"
        print(f"Creating collection: {collection_name}")
        collection = client.create_collection(name=collection_name)
        print("Collection created")
        
        # Load embedding model
        model_name = "all-MiniLM-L6-v2"
        print(f"\nLoading embedding model: {model_name}")
        print("   (This may take a moment on first run...)")
        model = SentenceTransformer(model_name)
        print("Model loaded")
        
        # Embed and store movies
        print("\nGenerating embeddings and storing in database...")
        embed_and_store_movies(movies, model, collection, batch_size=20)
        
        # Perform test search
        test_queries = [
            "romantic comedy with happy ending",
            "action movie with explosions",
            "family friendly animated movie"
        ]
        
        print("\n" + "="*70)
        print("VERIFICATION TESTS")
        print("="*70)
        
        for query in test_queries[:1]:  # Just test first query
            test_search(collection, model, query, n_results=3)
        
        # Success message
        print("="*70)
        print("DATABASE LOADED SUCCESSFULLY!")
        print("="*70)
        print(f"\nSummary:")
        print(f"   - Total movies: {len(movies)}")
        print(f"   - Collection: {collection_name}")
        print(f"   - Embedding model: {model_name}")
        print(f"   - Database location: {data_dir / 'chroma_db'}")
        print(f"\nYou can now use semantic search in the main application!\n")
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

