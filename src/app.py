from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import conf

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


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
    # id test : TW92aWU6MjkwNTgz
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
    seances = data.get(id).get('seances')



    return templates.TemplateResponse(
        request=request, name="movie.html", context={"title": title,
                                                     "synopsis": synopsis,
                                                     "posterUrl": posterUrl
                                                     
                                                     }
    )