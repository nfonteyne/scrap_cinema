from datetime import datetime

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

def clean_actor_dict(actors_infos:list) -> list:
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

def clean_dir_dict(directors_infos:list) -> list:
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
