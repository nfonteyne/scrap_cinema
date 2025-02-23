from datetime import datetime
import json

def load_movie_database(input_path:str) -> dict:
    with open(input_path, encoding='utf-8') as fh:
        data = json.load(fh)
    return data

def readable_showtimes(seances:dict) -> dict:
    show_dict = {}
    for key,_ in seances.items():
        seance_hours_by_cine = seances.get(key)
        if None == seance_hours_by_cine:
            continue
        if seance_hours_by_cine:
            cine = seance_hours_by_cine.get('cinemaName')
            for showtime in seance_hours_by_cine.get('showtimes'):
                readable_date = datetime.strptime(showtime, '%Y-%m-%dT%H:%M:%S').strftime('%A %m-%d')
                readable_time = datetime.strptime(showtime, '%Y-%m-%dT%H:%M:%S').strftime('%H:%M')
                if not readable_date in show_dict:
                    show_dict[readable_date] = {}
                if not cine in show_dict[readable_date]:
                    show_dict[readable_date][cine] = [readable_time]
                else:
                    show_dict[readable_date][cine].append(readable_time)
    return show_dict

def filter_showtimes_by_date(seances:dict, date_keep:datetime.date, threshold:bool=True):
    """
    function that remove the seances that have a date anterior to the date_keep argumeent in the seances dict
    theshold:bool -> if true remove only the date anterior to the date_keep, if false remove all the dates differents from the datekeep
    """
    for key,_ in seances.items():
        seance_hours_by_cine = seances.get(key)
        if None == seance_hours_by_cine:
            continue
        if seance_hours_by_cine:
            filtered_showtimes = []
            for showtime in seance_hours_by_cine.get('showtimes'):
                seance_date = datetime.strptime(showtime, '%Y-%m-%dT%H:%M:%S').date()
                if threshold:
                    if seance_date > date_keep:
                        filtered_showtimes.append(showtime)
                else:
                    if seance_date == date_keep:
                        filtered_showtimes.append(showtime)
            seance_hours_by_cine['showtimes'] = filtered_showtimes
    return seances

def filter_movies_by_date(data:dict, date_keep:datetime.date, threshold:bool=True):
    movie_day = {}
    for movie in data.keys():
        movie_infos = data.get(movie)
        if movie_infos:
            if movie_infos.get('seances'):
                movie_infos.get('seances')
                movie_infos['seances'] = filter_showtimes_by_date(movie_infos.get('seances'), date_keep, threshold)
                movie_infos['seances'] = readable_showtimes(movie_infos.get('seances'))
                if movie_infos.get('seances'):
                    movie_day[movie] = data.get(movie)
    return movie_day

def clean_actor_dict(actors_infos:list) -> list:
    if actors_infos:
        for actor_infos in actors_infos:
            if None == actor_infos.get('lastName'):
                actor_infos['lastname'] = ' '
            if None == actor_infos. get('firstName'):
                actor_infos['firstName'] = ' '
            if None == actor_infos.get('pictureUrl'):
                actor_infos['pictureUrl'] = 'http://localhost:8000/static/images/no_person.png'
            if None == actor_infos.get('position'):
                actor_infos['position'] = ' '
            else:
                actor_infos['position'] = 'ACTOR'
        return actors_infos
    else:
        return []

def clean_dir_dict(directors_infos:list) -> list:
    if directors_infos:
        for director_info in directors_infos:
            if None == director_info.get('lastName'):
                director_info['lastname'] = ' '
            if None == director_info. get('firstName'):
                director_info['firstName'] = ' '
            if None == director_info.get('pictureUrl'):
                director_info['pictureUrl'] = 'http://localhost:8000/static/images/no_person.png'
            if None == director_info.get('position'):
                director_info['position'] = ' '
            else:
                director_info['position'] = 'DIRECTOR'
        return directors_infos
    else:
        return []
