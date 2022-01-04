import uvicorn

from dynaconf import settings

if __name__ == "__main__":
    uvicorn.run("app.listener:app", reload=False)
