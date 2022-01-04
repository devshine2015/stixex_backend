import uvicorn

from dynaconf import settings

if __name__ == "__main__":
    uvicorn.run("app.api:app", host=settings.HOST, port=settings.PORT, debug=settings.DEBUG, reload=False)
