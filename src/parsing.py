import requests
from typing import Optional
import os
from datetime import datetime, date
import json
from conf import *



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

def parse_person(data: dict, is_actor: bool = False) -> Optional[dict]:
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
            
        return {
            'lastName':lastName,
            'firstName':firstName,
            'pictureUrl':get_url_from_nested(base, 'picture', 'url'),
            'position':position}
        
    except Exception:
        return None

def parse_seances(element: dict) -> Optional[dict]:
    """Parse seances data into dictionary format."""
    try:
        cinema_id = 'test'
        cinema_name = 'test'
        showtimes = element.get('showtimes', {}).get('original', [])
        
        if not all([cinema_id, cinema_name, showtimes]):
            return None
            
        return {
            'cinemaId': cinema_id,
            'cinemaName': cinema_name,
            'showtimes': [ele['startsAt'] for ele in showtimes]
        }
    except Exception:
        return None

def parse_stats(stats_data: Optional[dict]) -> Optional[dict]:
    """Parse stats data into Stats object."""
    if not stats_data:
        return None
    
    return {
        'userRating':{
            'score':stats_data.get('userRating', {}).get('score'),
            'count':stats_data.get('userRating', {}).get('count')
        },
        'pressRating':{
            'score':stats_data.get('pressReview', {}).get('score'),
            'count':stats_data.get('pressReview', {}).get('count')
        }}
    


def parse_seances(element: dict) -> Optional[dict]:
    """Parse seances data into a Seance object."""
    try:
        cinema_id = 'test'
        cinema_name = 'test'
        showtimes = element.get('showtimes', {}).get('original', [])
        
        if not all([cinema_id, cinema_name, showtimes]):
            return None
            
        # Convert string timestamps to datetime objects
        parsed_showtimes = [
            time['startsAt'] for time in showtimes
        ]
        
        return {
            'cinemaId':cinema_id,
            'cinemaName':cinema_name,
            'showtimes':parsed_showtimes
        }
    except Exception:
        return None

def parse_movie_data(element: dict) -> Optional[dict]:
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
        
        parsed_seances = parse_seances(element)
        
        return {movie_id: {
            'movieId':movie_id,
            'title':title,
            'synopsis':synopsis,
            'posterUrl':get_url_from_nested(movie, 'poster', 'url'),
            'runtime':runtime,
            'genre':[ele.get('translate') for ele in movie.get('genres', [])] if movie.get('genres') else None,
            'languages':movie.get('languages'),
            'stats':parse_stats(movie.get('stats')),
            'certificate':get_url_from_nested(movie, 'releases', 0, 'certificate', 'label'),
            'directors':parsed_credits if parsed_credits else None,
            'actors':parsed_actors if parsed_actors else None,
            'seances':parsed_seances}
        }
    except Exception:
        return None
    
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

if __name__ == "__main__":
    headers = {'Accept': 'application/json'}
    response = requests.get(os.getenv('URL_PATH'), headers=headers)



    structured_output = []
    for element in response.json()["results"]:
        movie_info = parse_movie_data(element)
        structured_output.append(movie_info)

    with open('./result.json', 'w', encoding='utf8') as fp:
        json.dump(structured_output, fp)