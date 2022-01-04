import uvicorn

from dynaconf import settings

if __name__ == "__main__":
    uvicorn.run("app.bet_checker:app", reload=False)
