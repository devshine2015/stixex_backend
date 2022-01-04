from http import HTTPStatus

from dynaconf import settings
from fastapi import APIRouter, HTTPException, Depends
from fastapi_sqlalchemy import db

from app.common.api_models import ApiAppSettingsModel
from app.common.db_models import AppSettings
from app.common.dependencies import no_cache
from app.model.api.user import User
from app.router.auth import get_current_active_user

app_settings_router = APIRouter()


@app_settings_router.get("/app_settings", status_code=200,
                         operation_id="getAppSettings",
                         response_model=ApiAppSettingsModel,
                         dependencies=[Depends(no_cache)])
async def get_app_settings(current_user: str = Depends(get_current_active_user)):
    settings = AppSettings.first()
    if not settings:
        raise HTTPException(HTTPStatus.NOT_FOUND, "App Settings not found")
    return settings


@app_settings_router.put("/app_settings/{id}", status_code=200,
                         operation_id="updateAppSettings",
                         response_model=ApiAppSettingsModel,
                         dependencies=[Depends(no_cache)])
async def update_app_settings(id: str, input: ApiAppSettingsModel, current_user: str = Depends(get_current_active_user)):
    app_settings = AppSettings.first()

    if not settings:
        raise HTTPException(HTTPStatus.NOT_FOUND, "App Settings not found")

    app_settings.update(bet_fee=input.bet_fee,
                        bet_payout=input.bet_payout,
                        maintenance=input.maintenance)
    AppSettings.session.commit()
    return app_settings
