from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import conf
from pathlib import Path

from helper import readable_showtimes, clean_actor_dict, clean_dir_dict
import locale

locale.setlocale(locale.LC_TIME, 'fr_FR')

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    with open(conf.DATABASE_PATH, encoding='utf-8') as fh:
        data = json.load(fh)
    response = templates.TemplateResponse(
        request=request,
        name="home.html",
        context={'movies_dict': data}
    )
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/date/{date}", response_class=HTMLResponse)
async def get_programmation_by_date(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html",
    )

@app.get("/movie/{id}", response_class=HTMLResponse)
async def get_movie_by_id(request: Request, id:str):
    with open(conf.DATABASE_PATH, encoding='utf-8') as fh:
        data = json.load(fh)
    # id test : W92aWU6MzE4NDkw
    title = data.get(id).get('title')
    synopsis = data.get(id).get('synopsis')
    posterUrl = data.get(id).get('posterUrl')
    runtime = data.get(id).get('runtime')
    genre = data.get(id).get('genre')
    # languages = data.get(id).get('languages')
    # stats = data.get(id).get('stats')
    # pressRating = data.get(id).get('pressRating')
    directors = clean_dir_dict(data.get(id).get('directors'))
    actors = clean_actor_dict(data.get(id).get('actors'))
    seances = readable_showtimes(data.get(id).get('seances'))

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
