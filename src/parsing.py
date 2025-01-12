import requests
from dataclasses import dataclass
from typing import List, Optional, Dict
from dotenv import load_dotenv
import os

load_dotenv()
@dataclass
class Rating:
    score: Optional[float] = None
    count: Optional[int] = None

@dataclass
class Stats:
    userRating: Rating
    pressRating: Rating

@dataclass
class Person:
    lastName: str
    firstName: str
    position: str
    pictureUrl: Optional[str] = None
    

@dataclass
class Movie:
    movieId: str
    title: str
    synopsis: str
    runtime: int
    posterUrl: Optional[str] = None
    genre: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    stats: Optional[Stats] = None
    certificate: Optional[str] = None
    directors: Optional[List[Person]] = None
    actors: Optional[List[Person]] = None

def get_url_from_nested(data: dict, *keys) -> Optional[str]:
    """Extract URL from nested dictionary structure."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current

def parse_person(data: dict, is_actor: bool = False) -> Optional[Person]:
    """Parse person data into Person object. Returns None if required fields are missing."""
    try:
        if is_actor:
            base = data.get('node', {}).get('actor', {})
        else:
            base = data.get('person', {})
        
        lastName = base.get('lastName')
        firstName = base.get('firstName')
        position = 'actor' if is_actor else data.get('position', {}).get('name')
        
        # Return None if any required field is missing
        if not all([lastName, firstName, position]):
            return None
            
        return Person(
            lastName=lastName,
            firstName=firstName,
            pictureUrl=get_url_from_nested(base, 'picture', 'url'),
            position=position
        )
    except Exception:
        return None

def parse_stats(stats_data: Optional[dict]) -> Optional[Stats]:
    """Parse stats data into Stats object."""
    if not stats_data:
        return None
    
    return Stats(
        userRating=Rating(
            score=stats_data.get('userRating', {}).get('score'),
            count=stats_data.get('userRating', {}).get('count')
        ),
        pressRating=Rating(
            score=stats_data.get('pressReview', {}).get('score'),
            count=stats_data.get('pressReview', {}).get('count')
        )
    )

def parse_movie_data(element: dict) -> Optional[Dict[str, Movie]]:
    """Parse movie data into Movie object. Returns None if required fields are missing."""
    try:
        movie = element.get('movie', {})
        movie_id = movie.get('id')
        title = movie.get('title')
        synopsis = movie.get('synopsis')
        runtime = movie.get('runtime')
        
        # Return None if any required field is missing
        if not all([movie_id, title, synopsis, runtime]):
            return None
            
        # Parse credits and actors, filtering out None values
        credits = movie.get('credits', [])
        parsed_credits = [p for p in (parse_person(ele) for ele in credits) if p is not None]
        
        actors = movie.get('cast', {}).get('edges', [])
        parsed_actors = [p for p in (parse_person(ele, is_actor=True) for ele in actors) if p is not None]
        
        return {movie_id: Movie(
            movieId=movie_id,
            title=title,
            synopsis=synopsis,
            posterUrl=get_url_from_nested(movie, 'poster', 'url'),
            runtime=runtime,
            genre=[ele.get('translate') for ele in movie.get('genres', [])] if movie.get('genres') else None,
            languages=movie.get('languages'),
            stats=parse_stats(movie.get('stats')),
            certificate=get_url_from_nested(movie, 'releases', 0, 'certificate', 'label'),
            directors=parsed_credits if parsed_credits else None,
            actors=parsed_actors if parsed_actors else None
        )}
    except Exception:
        return None

if __name__ == "__main__":
    headers = {'Accept': 'application/json'}
    response = requests.get(os.getenv('URL_PATH'), headers=headers)

    structured_output = []
    for element in response.json()["results"]:
        movie_info = parse_movie_data(element)
        structured_output.append(movie_info)


