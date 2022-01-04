import sentry_sdk
import socketio
from dynaconf import settings
from fastapi import FastAPI
from fastapi_sqlalchemy import db
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.common.db_models import DBMiddleware, Base, AppSettings
from app.common.routers import default_router, event_router, misc_router
from app.router.app_settings import app_settings_router
from app.router.auth import auth_router
from app.router.chain_events import chain_events_router
from app.router.users import users_router
from app.router.bets import bets_router
from app.router.logs import logs_router
from app.common.utils import get_custom_openapi
from app.router.withdraw_requests import withdraw_requests_router

app = FastAPI(
    title="Stixex API",
    docs_url='/docs',
    version="0.0.1",
    debug=settings.DEBUG,
)

mgr = socketio.AsyncRedisManager('redis://')
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', client_manager=mgr)
sio_app = socketio.ASGIApp(sio)


@sio.event
def connect(sid, environ):
    print('connect ', sid)


@sio.on('joinRoom')
def join_room(sid, data):
    room_name = data['roomName']
    for room in sio.rooms(sid):
        sio.leave_room(sid, room)
        logger.debug(f'Room {room} leaved')
    sio.enter_room(sid, room_name)
    logger.debug(f'joined {sid} {room_name}')


@sio.event
def disconnect(sid):
    print('disconnect ', sid)


app.mount("/sio", sio_app)

app.include_router(
    default_router,
    prefix="",
    tags=["Default"]
)

app.include_router(
    misc_router,
    prefix="",
    tags=["Misc"]
)

app.include_router(
    event_router,
    prefix="",
    tags=["Event"]
)

app.include_router(
    app_settings_router,
    prefix="",
    tags=["Settings"]
)

app.include_router(
    users_router,
    prefix="",
    tags=["Users"]
)

app.include_router(
    bets_router,
    prefix="",
    tags=["Bets"]
)

app.include_router(
    logs_router,
    prefix="",
    tags=["Logs"]
)

app.include_router(
    chain_events_router,
    prefix="",
    tags=["Events"]
)

app.include_router(
    withdraw_requests_router,
    prefix="",
    tags=["Withdraw"]
)

app.include_router(
    auth_router,
    prefix="",
    tags=["Auth"]
)

app.mount("/static", StaticFiles(directory=settings.STATIC_PATH), name="static")


@app.on_event('startup')
async def startup():
    app.openapi = get_custom_openapi(app)
    app.add_middleware(DBMiddleware, db_url=settings.DATABASE_URL)
    with db():
        Base.metadata.create_all(db.session.get_bind())
        AppSettings.set_session(db.session)
        app_settings = AppSettings().instance
        if not app_settings:
            app_settings = AppSettings.create()
            db.session.commit()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.USE_SENTRY:
        sentry_sdk.init(dsn=settings.SENTRY_KEY,
                        traces_sample_rate=1.0)
