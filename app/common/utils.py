import math
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import redis
import socketio

import requests
from dynaconf import settings
from fastapi.openapi.utils import get_openapi


def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def process_schema(openapi_schema):
    enums = {}
    for schema in openapi_schema['components']['schemas'].values():
        properties = schema.get('properties', None)
        if properties:
            for prop in schema['properties']:
                if 'enum' in schema['properties'][prop]:
                    name = prop[0].capitalize() + prop[1:]
                    values = schema['properties'][prop]['enum']
                    enums[name] = values
                    schema['properties'][prop] = {"$ref": f"#/components/schemas/{name}"}
    for path in openapi_schema['paths']:
        for r in openapi_schema['paths'][path]:
            if 'parameters' in openapi_schema['paths'][path][r]:
                for param in openapi_schema['paths'][path][r]['parameters']:
                    if 'enum' in param['schema']:
                        name = param['name'][0].capitalize() + param['name'][1:]
                        values = param['schema']['enum']
                        enums[name] = values
                        param['schema'] = {"$ref": f"#/components/schemas/{name}"}
    for name in enums:
        openapi_schema['components']['schemas'][name] = {
            "type": "string",
            "enum": enums[name]
        }
    return openapi_schema


def get_custom_openapi(app):
    def custom_openapi():
        if not app.openapi_schema:
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes
            )
            openapi_schema = process_schema(openapi_schema)
            app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi


def get_nearest_interval_start(time_frame):
    now = datetime.utcnow()
    return now.replace(second=0, microsecond=0) + timedelta(minutes=time_frame - now.minute % time_frame)


@lru_cache(maxsize=64)
def get_history_by_asset(time_frame, asset, start_time, end_time):
    from app.common.api_models import AssetCandle
    response = requests.get(
        f'https://www.binance.com/api/v3/klines?'
        f'symbol={asset}&'
        f'interval={time_frame}m&' + (
            f'endTime={int(end_time.timestamp())}000&'
            f'startTime={int(start_time.timestamp())}000&' if start_time and end_time else ''
        ) +
        f'limit=10').json()
    if len(response):
        return AssetCandle(start=response[0][0], end=response[0][6], time_frame=time_frame,
                           open=response[0][1],
                           close=response[0][4])
    else:
        return AssetCandle(start=start_time, end=end_time, time_frame=time_frame, open=0,
                           close=0)


sio = socketio.RedisManager(settings.REDIS_URL, write_only=True)


def emit(room, event, data):
    if not isinstance(data, dict):
        data = data.json()
    sio.emit(event, data=data, room=room)


def amount_formatter(amount):
    amount = amount or 0
    amount = f"{amount:0>19}"
    return f"{amount[:-18]}.{amount[-18:-12]}"


def round_integer(amount: int, numbers_count: int):
    return math.floor(amount / 10 ** numbers_count) * 10 ** numbers_count


redis_client = redis.StrictRedis(decode_responses=True)
