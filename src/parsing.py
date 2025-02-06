import requests
from typing import Optional
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
    return str(current)

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
    


def parse_screening(element: dict, cinema_id, cinema_name) -> Optional[dict]:
    """Parse seances data into a Seance object."""
    try:
        showtimes_original = element.get('showtimes', {}).get('original', [])
        showtimes_local = element.get('showtimes', {}).get('local', [])
        showtimes = [*showtimes_original,*showtimes_local]
        
        if not all([cinema_id, cinema_name, showtimes]):
            return {}
            
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
        
        parsed_seances = parse_screening(element, cinema_id, cinema_name)
        
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
            'seances':parsed_seances}
        }
    except Exception:
        return None
       
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def update_seance_info(movie_database_seance:dict, seances_info:dict):
    if seances_info:
        seances_info_key = next(iter(seances_info))
        if seances_info_key in movie_database_seance:
            showtimes_list_new_cine = seances_info.get(seances_info_key).get('showtimes')
            for showtime in showtimes_list_new_cine:
                movie_database_seance.get(seances_info_key).get('showtimes').append(showtime)
        else:
            movie_database_seance[seances_info_key]=seances_info.get(seances_info_key)
    
    

if __name__ == "__main__":
    dict_cinema = conf.CINEMAS
    url_root = conf.URL_ROOT
    database_path = conf.DATABASE_PATH

    # Initialize empty database if none exists
    movie_database = {}

    # Process each day in range
    for i in range(7):
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
            response = requests.get(url_path, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    for element in data["results"]:
                        movie_data = parse_movie_data(element,cinema_info)
                        if movie_data:
                            movie_key = next(iter(movie_data))
                            if movie_key in movie_database:
                                database_seance_info = movie_database.get(movie_key).get('seances')
                                new_movie_seances_info = movie_data.get(movie_key).get('seances')
                                update_seance_info(database_seance_info, new_movie_seances_info)
                            else:
                                movie_database.update(movie_data) 

    if movie_database:
        try:
            with open(database_path, 'w', encoding='utf8') as fp:
                json.dump(movie_database, fp, default=json_serial, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving database: {str(e)}")
                            
