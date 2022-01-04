from http import HTTPStatus
from typing import Optional
from urllib.parse import quote_plus

from fastapi import Header, HTTPException
from fastapi import Response
from loguru import logger
from starlette.requests import Request

from app.common.db_models import DbUser, DbChainEvent
from app.common.enums import Currency, SocketEvents
from app.model.api.chain_event import ChainEvent


class SignedRequestOperations:
    @classmethod
    def get_signature_creation_url(cls, request):
        return f'{request.url.scheme}://{request.url.netloc}/signature?{"&".join(["args=" + quote_plus(str(value)) for key, value in sorted(request.query_params.items(), key=lambda x: x[0])])}'

    @classmethod
    def get_signer(cls, signature, request):
        from web3.auto import w3
        from eth_account.messages import encode_defunct
        message = "|".join(str(value) for key, value in sorted(request.query_params.items(), key=lambda k: k[0]))
        logger.debug(message)
        signer = w3.eth.account.recover_message(
            encode_defunct(text=message),
            signature=signature)
        return signer

    @classmethod
    def get_signer_from_signature(cls, request: Request, signature: Optional[str] = Header(None)):
        if not signature:
            raise HTTPException(HTTPStatus.UNAUTHORIZED, cls.get_signature_creation_url(request))
        signer = cls.get_signer(signature, request)
        user = DbUser.where(address=signer, network_id=request.query_params['network_id']).first()
        return user


class ChainEventOperations:
    @classmethod
    def create_event_db_record(cls, request: Request,
                               transaction_hash: str, name: str, network_id: int, address: str, block: int,
                               currency: Currency,
                               account: str = None,
                               amount: int = None):
        user = DbUser.where(address=account, network_id=network_id).first()
        if not user:
            user = DbUser.create(address=account, network_id=network_id)
        if not DbChainEvent.where(network_id=network_id, transaction_hash=transaction_hash,
                                  name=name).first():
            chain_event = DbChainEvent.create(
                contract_address=address,
                network_id=network_id,
                transaction_hash=transaction_hash,
                block=block,
                amount=amount,
                currency=currency,
                user_address=account,
                name=name,
                data=dict(request.query_params)
            )
            DbChainEvent.session.commit()
            user.emit(SocketEvents.CHAIN_EVENT_CREATED, ChainEvent.from_orm(chain_event))
        else:
            raise HTTPException(HTTPStatus.OK, 'Already processed')


def no_cache(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = '0'
