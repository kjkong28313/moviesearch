################################################################################
# FILE: extractmovie/createindexes.py
# LOCATION: extractmovie/ directory
################################################################################

"""
Create inverted indexes for fast structured search
Indexes: actor, director, genre, company, year
"""

from pathlib import Path
import json
from collections import defaultdict
from typing import Dict, List


class IndexBuilder:
    """Build and save inverted indexes for movie search"""
    
    def __init__(self):
        self.indexes = {
            "actor": defaultdict(list),
            "director": defaultdict(list),
            "genre": defaultdict(list),
            "company": defaultdict(list),
            "year": defaultdict(list),
        }
    
    def build_indexes(self, movies: List[Dict]) -> Dict[str, Dict]:
        """
        Build all indexes from movie data
        
        Args:
            movies: List of movie metadata dictionaries
            
        Returns:
            Dictionary of indexes
        """
        print(f"Building indexes for {len(movies)} movies...")
        
        for idx, movie in enumerate(movies, 1):
            # Extract basic info
            title = movie.get("title", "")
            release_year = movie.get("release_date", "").split("-")[0] if movie.get("release_date") else ""
            
            # Year index
            if release_year and release_year.isdigit():
                self.indexes["year"][release_year].append(movie)
            
            # Actor index
            actors = movie.get("actors", [])
            if isinstance(actors, list):
                for actor in actors:
                    if actor:
                        self.indexes["actor"][actor.lower()].append(movie)
            
            # Director index
            director = movie.get("director")
            if director:
                self.indexes["director"][director.lower()].append(movie)
            
            # Production company index
            companies = movie.get("production_companies", [])
            if isinstance(companies, list):
                for company in companies:
                    if company:
                        self.indexes["company"][company.lower()].append(movie)
            
            # Genre index
            genres = movie.get("genres", [])
            if isinstance(genres, list):
                for genre in genres:
                    if genre:
                        self.indexes["genre"][genre.lower()].append(movie)
            
            # Progress indicator
            if idx % 100 == 0:
                print(f"  Processed {idx}/{len(movies)} movies...")
        
        print(f"Completed building all indexes")
        return self.indexes
    
    def save_indexes(self, output_dir: Path):
        """
        Save indexes to JSON files
        
        Args:
            output_dir: Directory to save index files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for key, index in self.indexes.items():
            filepath = output_dir / f"{key}_index.json"
            
            # Convert defaultdict to regular dict for JSON serialization
            regular_dict = {k: v for k, v in index.items()}
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(regular_dict, f, indent=2, ensure_ascii=False)
            
            print(f"  Saved {key} index to {filepath} ({len(regular_dict)} entries)")
    
    def print_statistics(self):
        """Print statistics about the indexes"""
        print("\n" + "="*60)
        print("INDEX STATISTICS")
        print("="*60)
        
        stats = []
        for key, index in self.indexes.items():
            count = len(index)
            stats.append((key.capitalize(), count))
        
        # Sort by count descending
        stats.sort(key=lambda x: x[1], reverse=True)
        
        for name, count in stats:
            print(f"  {name:20s}: {count:>6,} unique entries")
        
        print("="*60 + "\n")


def load_movie_data(filepath: Path) -> List[Dict]:
    """
    Load movie data from JSON file
    
    Args:
        filepath: Path to movie JSON file
        
    Returns:
        List of movie dictionaries
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            movies = json.load(f)
        print(f"Loaded {len(movies)} movies from {filepath}")
        return movies
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return []
    except Exception as e:
        print(f"Error loading movie data: {e}")
        return []


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("MOVIE INDEX BUILDER")
    print("="*60 + "\n")
    
    # Setup paths
    script_path = Path(__file__).resolve().parent
    data_dir = script_path.with_name("data")
    data_path = data_dir / "tmdb_movies_full_credits.json"
    
    # Load movie data
    movies = load_movie_data(data_path)
    if not movies:
        print("\nNo movies loaded. Exiting.")
        return 1
    
    # Build indexes
    builder = IndexBuilder()
    indexes = builder.build_indexes(movies)
    
    # Save indexes
    print(f"\nSaving indexes to {data_dir}...")
    builder.save_indexes(data_dir)
    
    # Print statistics
    builder.print_statistics()
    
    # Verification
    print("VERIFICATION")
    print("="*60)
    print("Sample entries from each index:")
    print()
    
    for key, index in indexes.items():
        if index:
            sample_key = list(index.keys())[0]
            sample_count = len(index[sample_key])
            print(f"  {key.capitalize()}: '{sample_key}' -> {sample_count} movie(s)")
    
    print("\nIndex building completed successfully!\n")
    return 0


if __name__ == "__main__":
    exit(main())


