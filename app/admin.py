import sentry_sdk
from dynaconf import settings
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.menu import MenuLink
from flask_basicauth import BasicAuth
from flask_sqlalchemy import SQLAlchemy

from app.common.api_models import Withdraw, User
from app.common.enums import SocketEvents
from app.common.views import *
from app.common.db_models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['BASIC_AUTH_USERNAME'] = settings.AUTH_LOGIN
app.config['BASIC_AUTH_PASSWORD'] = settings.AUTH_PASSWORD
app.config['BASIC_AUTH_FORCE'] = True
admin = Admin(app, url='/', index_view=HomeStatsView(url="/"), name="Stixex Admin", template_mode="bootstrap3")
db = SQLAlchemy(app)
Base.set_session(db.session)

basic_auth = BasicAuth(app)


@app.route('/approve', methods=['POST'])
def approve():
    withdraw_id = request.form.get('id')
    withdraw = DbWithdraw.where(id=withdraw_id).first()
    if withdraw.status == WithdrawStatus.PENDING:
        if settings.NETWORKS[withdraw.network_id].ADMIN.lower() == request.form['user_address'].lower():
            withdraw.approve(request.form.get('signature'))
            db.session.commit()
            flash(
                f'Withdraw {withdraw.id} from {withdraw.user_address} '
                f'for {withdraw.amount / 10 ** 18} {withdraw.currency} approved',
                'success')
            withdraw.user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))
        else:
            flash(
                f'Withdraw {withdraw.id} from {withdraw.user_address} '
                f'for {withdraw.amount / 10 ** 18} {withdraw.currency} approve fail. You ({request.form["user_address"]}) not admin in this network ({withdraw.network_id}).',
                'error')
    else:
        flash(
            f'Withdraw {withdraw.id} from {withdraw.user_address} '
            f'for {withdraw.amount / 10 ** 18} {withdraw.currency} approve fail. '
            f'Withdraw status {withdraw.status}',
            'error')

    return redirect(request.form.get('redirect_uri'))


@app.route('/pending_withdraw_count', methods=['GET'])
def pending_withdraw_count():
    return str(DbWithdraw.where(status=WithdrawStatus.PENDING).count())


@app.route('/reject', methods=['POST'])
def reject():
    withdraw_id = request.form.get('id')
    withdraw = DbWithdraw.where(id=withdraw_id).first()
    if withdraw.status == WithdrawStatus.PENDING or withdraw.status == WithdrawStatus.APPROVED:
        withdraw.reject(request.form.get('reject_message'))
        db.session.commit()
        flash(
            f'Withdraw {withdraw.id} from {withdraw.user_address} '
            f'for {withdraw.amount / 10 ** 18} {withdraw.currency} rejected',
            'success')
        withdraw.user.emit(SocketEvents.WITHDRAW_STATE_CHANGED, Withdraw.from_orm(withdraw))
        withdraw.user.emit(SocketEvents.USER_STATE_CHANGED, User.from_orm(withdraw.user))
    else:
        flash(
            f'Withdraw {withdraw.id} from {withdraw.user_address} '
            f'for {withdraw.amount / 10 ** 18} {withdraw.currency} reject fail. Withdraw status {withdraw.status}',
            'error')
    return redirect(request.form.get('redirect_uri'))


def main():
    app.run(host=settings.ADMIN_HOST,
            port=settings.ADMIN_PORT,
            debug=False)


admin.add_view(UsersView(DbUser, db.session, 'Users',
                         menu_icon_type='glyph',
                         menu_icon_value='glyphicon-user'
                         ))
admin.add_view(BetsView(DbBet, db.session, 'Bets',
                        menu_icon_type='glyph',
                        menu_icon_value='glyphicon-tags'))
admin.add_view(WithdrawView(DbWithdraw, db.session, 'Withdraw Requests',
                            menu_class_name='withdraws-menu-item',
                            menu_icon_type='glyph',
                            menu_icon_value='glyphicon-export'))
admin.add_view(ChainEventView(DbChainEvent, db.session, 'Chain Events',
                              menu_icon_type='glyph',
                              menu_icon_value='glyphicon-send'
                              ))

admin.add_view(AppSettingsView(AppSettings, db.session,
                               menu_icon_type='glyph',
                               menu_icon_value='glyphicon-cog'))
admin.add_link(MenuLink(name='', category='', url='#', class_name='metamask_button'))
if __name__ == "__main__":
    if settings.USE_SENTRY:
        sentry_sdk.init(dsn=settings.SENTRY_KEY,
                        traces_sample_rate=0.2)
    main()
