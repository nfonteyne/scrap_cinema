from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import conf
from pathlib import Path
from datetime import datetime

import locale
locale.setlocale(locale.LC_TIME, 'fr_FR')

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

templates = Jinja2Templates(directory="templates")

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
                readable_time = datetime.strptime(showtime, '%Y-%m-%dT%H:%M:%S').strftime('%H:%M:%S')
                if not readable_date in show_dict:
                    show_dict[readable_date] = {}
                if not cine in show_dict[readable_date]:
                    show_dict[readable_date][cine] = [readable_time]
                else:
                    show_dict[readable_date][cine].append(readable_time)
    return show_dict

@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id}
    )

@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html",
    )
@app.get("/movie/{id}", response_class=HTMLResponse)
async def get_movie_by_id(request: Request, id:str):
    with open(conf.DATABASE_PATH, encoding='utf-8') as fh:
        data = json.load(fh)
    # id test : TW92aWU6MzE4NDkw
    print(data.get(id))
    title = data.get(id).get('title')
    synopsis = data.get(id).get('synopsis')
    posterUrl = data.get(id).get('posterUrl')
    runtime = data.get(id).get('runtime')
    genre = data.get(id).get('genre')
    languages = data.get(id).get('languages')
    stats = data.get(id).get('stats')
    pressRating = data.get(id).get('pressRating')
    directors = data.get(id).get('directors')
    actors = data.get(id).get('actors')
    seances = readable_showtimes(data.get(id).get('seances'))
    print(seances)

    return templates.TemplateResponse(
        request=request, name="movie.html", context={"title": title,
                                                     "synopsis": synopsis,
                                                     "posterUrl": posterUrl,
                                                     "runtime": runtime,
                                                     "genre": genre,
                                                     "directors": directors, "actors": actors,
                                                     "seances": seances
                                                     }
    )
