import asyncio
import json
import sys
import traceback
from pprint import pformat
from configparser import ConfigParser
import aiojobs
import requests_async as requests
import sentry_sdk
from dynaconf import settings
from loguru import logger
from sentry_sdk import capture_exception
from web3 import Web3, WebsocketProvider
from web3._utils.events import construct_event_topic_set, get_event_data
from web3.exceptions import LogTopicError

from app.common.enums import Currency

import nest_asyncio
nest_asyncio.apply()

if settings.USE_SENTRY:
    sentry_sdk.init(settings.SENTRY_KEY,
                    traces_sample_rate=0.2)

ENABLED_NETWORK_NUMBERS = settings.ENABLED_NETWORK_NUMBERS


async def load_event_signatures(network_number: int):
    tracked_events = {}

    def prepare_events(contract):
        with open(contract['abi'], 'r') as file:
            abi = json.loads(file.read())
            for element in abi:
                if element['type'] == 'event':
                    topic = construct_event_topic_set(element)[0]
                    if element['name'] in contract['tracked_event_names']:
                        if topic not in tracked_events:
                            tracked_events[topic] = element
                            logger.info(f'Added event {contract["abi"]} - {element["name"]}')
                        if 'addresses' not in tracked_events[topic]:
                            tracked_events[topic]['addresses'] = []
                        tracked_events[topic]['addresses'].append(contract['address'])

    prepare_events(settings.NETWORKS[network_number].ETH_CONTRACT)
    prepare_events(settings.NETWORKS[network_number].USDT_CONTRACT)

    return tracked_events


async def process_event(event, network_id, network_number: int):
    logger.info(f"\r\n{event.event} - {event.address}\r\n{pformat(dict(event.args))}")
    payload = {
        key.replace("_", ""): value.hex() if isinstance(value, bytes) else value
        for key, value in event.args.items()
    }
    currency = None

    if event.address.lower() == settings.NETWORKS[network_number].ETH_CONTRACT['address'].lower():
        currency = Currency.ETH
    if event.address.lower() == settings.NETWORKS[network_number].USDT_CONTRACT['address'].lower():
        currency = Currency.USDT

    payload.update({
        'network_id': network_id,
        'transaction_hash': event.transactionHash.hex(),
        'name': event.event,
        'block': event.blockNumber,
        'address': event.address,
        'currency': currency
    })
    try:
        logger.info(f"Event requesting event")
        if event.event.lower()!="deposited" or event.event.lower()!="withdraw":
            response = await requests.post(f"{settings.API_EVENT_URL}{event.event.lower()}", params=payload)
            if response.status_code == 200:
                logger.info(f"Event {event.event} sent")
            else:
                raise Exception("Bad response", response.text)
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        raise


async def process_network(network_number: int):
    W3 = Web3(Web3.WebsocketProvider(settings.NETWORKS[network_number].NODE_URL, websocket_kwargs={'max_size': 999999999999}))
    config_filename = f'listener_network_{network_number}.ini'
    config = ConfigParser()
    config.read(config_filename)
    if not config.has_section('default'):
        config.add_section('default')
    if not config.has_option('default', 'last_block_number'):
        config.set('default', 'last_block_number', str(W3.eth.blockNumber - 1))
    with open(config_filename, 'w') as f:
        config.write(f)
    last_block_number = int(config.get('default', 'last_block_number'))
    tracked_events = await load_event_signatures(network_number)

    while True:
        try:
            latest_block = W3.eth.blockNumber

            if latest_block > last_block_number:
                network_id = W3.eth.chainId

                logger.info(f'Block {last_block_number + 1}')

                log_items = W3.eth.filter({
                    'fromBlock': last_block_number + 1,
                    'toBlock': last_block_number + 1
                }).get_all_entries()
                for log_item in log_items:
                    for topic in log_item['topics']:
                        if topic.hex() in tracked_events:
                            print(topic.hex())
                            try:
                                parsed_event = get_event_data(tracked_events[topic.hex()], log_item)
                                if parsed_event['address'] in tracked_events[topic.hex()]['addresses']:
                                    await process_event(parsed_event, network_id, network_number)
                            except LogTopicError:
                                logger.debug('Bad event')
                config.set('default', 'last_block_number', str(last_block_number + 1))
                with open(config_filename, 'w') as f:
                    config.write(f)
                last_block_number += 1
        except:
            logger.error(traceback.format_exc())
            W3 = Web3(WebsocketProvider(settings.NETWORKS[network_number].NODE_URL, websocket_kwargs={'max_size': 999999999999}))
            await asyncio.sleep(settings.DELAY)
        finally:
            if latest_block <= last_block_number:
                await asyncio.sleep(settings.DELAY)

loop = asyncio.get_event_loop()
for net in ENABLED_NETWORK_NUMBERS:
    loop.create_task(process_network(net))
loop.run_forever()
