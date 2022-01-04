import time
import traceback
from datetime import datetime, timezone

import sentry_sdk
from dynaconf import settings
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.common.db_models import DbBet, Base
from app.common.enums import BetStatus, SocketEvents 
from app.common.utils import get_history_by_asset
from app.common.api_models import Bet, User
print("================================")
if settings.USE_SENTRY:
    sentry_sdk.init(dsn=settings.SENTRY_KEY,
                    traces_sample_rate=0.2)

engine = create_engine(settings.DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))
print("good checking-----------")
while True:
    logger.info('Start cycle...')
    session = Session()
    Base.set_session(session)
    print("checking-----------")
    for bet in DbBet.where(status=BetStatus.PROCESSING).all():
        try:
            if bet.interval_end <= datetime.utcnow():
                logger.info(f'Processing bet {bet.id}')
                candle = get_history_by_asset(bet.time_frame, bet.asset,
                                              bet.interval_start.replace(tzinfo=timezone.utc),
                                              bet.interval_end.replace(tzinfo=timezone.utc))
                bet.process_result(candle)
                session.commit()
                bet.user.emit(SocketEvents.BET_STATE_CHANGED, Bet.from_orm(bet))
                bet.user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(bet.user))
                logger.info(f'Bet {bet.id} processed')
        except:
            logger.error(traceback.format_exc())
    time.sleep(3)
