import requests
from typing import Optional
import os
from datetime import datetime, date, timedelta
import json
import conf



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
    


def parse_seances(element: dict, cinema_id, cinema_name) -> Optional[dict]:
    """Parse seances data into a Seance object."""
    try:
        showtimes_original = element.get('showtimes', {}).get('original', [])
        showtimes_local = element.get('showtimes', {}).get('local', [])
        showtimes = [*showtimes_original,*showtimes_local]
        
        if not all([cinema_id, cinema_name, showtimes]):
            return None
            
        # Convert string timestamps to datetime objects
        parsed_showtimes = [
            time['startsAt'] for time in showtimes
        ]
        
        return {cinema_id :
                {
            'cinemaName':cinema_name,
            'showtimes':parsed_showtimes
                }
                }
    except Exception:
        return None

def parse_movie_data(element: dict, cinema_infos) -> Optional[dict]:
    """Parse movie data into Movie object. Returns None if required fields are missing."""
    try:
        cinema_id = cinema_infos['cinema_id']
        cinema_name = cinema_infos['cinema_name']
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
        
        parsed_seances = parse_seances(element, cinema_id, cinema_name)
        
        return {movie_id: {
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
            'seances':[parsed_seances]}
        }
    except Exception:
        return None
    
def merge_movie_data(existing_data: dict, new_movie: dict) -> dict:
    """Merge new movie data with existing data, properly organizing seances by cinema"""
    if not new_movie:
        return existing_data
        
    try:
        movie_id = list(new_movie.keys())[0]
        movie_data = new_movie[movie_id]
        
        # Safely get seances data
        seances_list = movie_data.get('seances', [])
        if not seances_list:
            return existing_data
            
        new_seance = seances_list[0]  # Get first seance entry
        if not new_seance:
            return existing_data
            
        if movie_id in existing_data:
            # Movie exists, update/append seances for specific cinema
            for seance in seances_list:
                if not seance:  # Skip if seance is None
                    continue
                    
                cinema_id = list(seance.keys())[0]
                
                if 'seances' not in existing_data[movie_id]:
                    existing_data[movie_id]['seances'] = {}
                    
                if cinema_id in existing_data[movie_id]['seances']:
                    # Append new showtimes to existing cinema
                    existing_showtimes = existing_data[movie_id]['seances'][cinema_id]['showtimes']
                    new_showtimes = seance[cinema_id]['showtimes']
                    # Create a set to remove duplicates
                    unique_showtimes = list(set(existing_showtimes + new_showtimes))
                    existing_data[movie_id]['seances'][cinema_id]['showtimes'] = sorted(unique_showtimes)
                else:
                    # Add new cinema entry
                    existing_data[movie_id]['seances'][cinema_id] = seance[cinema_id]
        else:
            # New movie, initialize with reorganized seances
            seances_dict = {}
            for seance in seances_list:
                if seance:  # Only process if seance is not None
                    cinema_id = list(seance.keys())[0]
                    seances_dict[cinema_id] = seance[cinema_id]
            
            movie_data['seances'] = seances_dict
            existing_data[movie_id] = movie_data
            
        return existing_data
        
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error in merge_movie_data: {str(e)}")
        return existing_data
    
def load_existing_database(file_path: str) -> dict:
    """Load existing movie database if it exists, create new one if it doesn't"""
    try:
        with open(file_path, 'r', encoding='utf8') as fp:
            return json.load(fp)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty dictionary if file doesn't exist or is invalid
        return {}

def process_cinemas(dict_cinema: dict, url_root: str, days_range: int = 2) -> dict:
    """Process multiple cinemas and dates, creating or updating the movie database"""
    database_path = './result.json'
    
    # Initialize empty database if none exists
    movie_database = {}
    
    # Process each day in range
    for i in range(days_range):
        day_date = (date.today() + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Process each cinema
        for cinema_name, cinema_id in dict_cinema.items():
            url_path = f"{url_root}{cinema_id}/d-{day_date}/"
            
            cinema_info = {
                'cinema_id': cinema_id,
                'cinema_name': cinema_name,
                'url': url_path
            }
            
            # Make API request
            headers = {'Accept': 'application/json'}
            try:
                response = requests.get(url_path, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if "results" in data:
                        for element in data["results"]:
                            movie_info = parse_movie_data(element, cinema_info)
                            if movie_info:
                                movie_database = merge_movie_data(movie_database, movie_info)
                else:
                    print(f"Failed to fetch data for {cinema_name} on {day_date}: Status code {response.status_code}")
            except requests.RequestException as e:
                print(f"Error fetching data for {cinema_name}: {str(e)}")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {cinema_name}: {str(e)}")
    
    # Save database only if we have data
    if movie_database:
        try:
            with open(database_path, 'w', encoding='utf8') as fp:
                json.dump(movie_database, fp, default=json_serial)
        except IOError as e:
            print(f"Error saving database: {str(e)}")
    
    return movie_database
    
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

if __name__ == "__main__":
    dict_cinema = conf.CINEMAS
    url_root = conf.URL_ROOT
    
    # Process all cinemas and create/update database
    updated_database = process_cinemas(dict_cinema, url_root)