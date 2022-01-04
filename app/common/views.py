import json
from pprint import pformat

from dynaconf import settings
from flask import request, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from web3 import Web3, WebsocketProvider
from web3.auto import w3
from werkzeug.datastructures import ImmutableMultiDict

from app.common import db_models
from app.common.db_models import AppSettings, DbBet
from app.common.enums import WithdrawStatus, Currency, BetResult
from app.common.utils import amount_formatter


class UsersView(ModelView):
    column_searchable_list = ['address']
    column_filters = ['address', 'network_id', 'eth_balance', 'usdt_balance']
    fast_mass_delete = False
    action_disallowed_list = ['delete']
    can_create = False
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = ['address', 'eth_balance', 'usdt_balance', 'network_id', 'eth_withdraw_requested',
                   'usdt_withdraw_requested', 'created']
    column_details_list = ['address', 'eth_balance', 'usdt_balance', 'network_id', 'created', 'eth_withdraw_requested',
                           'usdt_withdraw_requested', 'win_loss_ratio', 'deposits_withdraws']
    column_formatters = {
        'created': lambda v, c, m, p: m.created.strftime("%Y/%m/%d %H:%M:%S"),
        'eth_balance': lambda v, c, m, p: amount_formatter(m.eth_balance),
        'usdt_balance': lambda v, c, m, p: amount_formatter(m.usdt_balance),
        # 'eth_balance_fee':lambda v, c, m, p: amount_formatter(m.eth_balance_fee),
        # 'usdt_balance_fee': lambda v, c, m, p: amount_formatter(m.usdt_balance_fee),

    }


class BetsView(ModelView):
    column_labels = {'user_address': 'User Address'}
    column_searchable_list = ['user_address']
    can_edit = False
    can_create = False
    can_delete = False
    can_view_details = True
    column_default_sort = ('created', True)
    column_list = ['user', 'amount', 'paid_amount', 'fee_amount', 'currency', 'asset', 'result', 'network_id',
                   'created']
    column_filters = ['user_address', 'amount', 'currency', 'paid_amount', 'network_id', 'created', 'status',
                      'time_frame', 'choice', 'result', 'asset']
    column_formatters = {
        'created': lambda v, c, m, p: m.created.strftime("%Y/%m/%d %H:%M:%S"),
        'amount': lambda v, c, m, p: amount_formatter(m.amount),
        'fee_amount': lambda v, c, m, p: amount_formatter(m.fee_amount),
        'paid_amount': lambda v, c, m, p: amount_formatter(m.paid_amount),
    }
    page_size = 50

    list_template = 'admin/model/summary_list.html'

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        if execute:
            return super().get_list(page, sort_column, sort_desc, search, filters,
                                    execute, page_size)
        else:
            joins = {}
            count_joins = {}

            query = self.get_query()
            count_query = self.get_count_query() if not self.simple_list_pager else None

            # Ignore eager-loaded relations (prevent unnecessary joins)
            # TODO: Separate join detection for query and count query?
            if hasattr(query, '_join_entities'):
                for entity in query._join_entities:
                    for table in entity.tables:
                        joins[table] = None

            # Apply search criteria
            if self._search_supported and search:
                query, count_query, joins, count_joins = self._apply_search(query,
                                                                            count_query,
                                                                            joins,
                                                                            count_joins,
                                                                            search)

            # Apply filters
            if filters and self._filters:
                query, count_query, joins, count_joins = self._apply_filters(query,
                                                                             count_query,
                                                                             joins,
                                                                             count_joins,
                                                                             filters)

            # Calculate number of rows if necessary
            count = count_query.scalar() if count_query else None

            # Auto join
            for j in self._auto_joins:
                query = query.options(joinedload(j))

            # Execute if needed
            if execute:
                query = query.all()

            return count, query

    def get_query_with_filters(self):
        view_args = self._get_list_extra_args()
        q = self.get_list(view_args.page, None, None,
                          view_args.search, view_args.filters, execute=False)[1]
        return q

    def total_amount(self):
        # this should take into account any filters/search inplace
        return self.get_query_with_filters().with_entities(func.sum(DbBet.amount)).scalar()

    def total_paid_amount(self):
        # this should take into account any filters/search inplace
        return self.get_query_with_filters().with_entities(func.sum(DbBet.paid_amount)).scalar()

    def total_fee_amount(self):
        # this should take into account any filters/search inplace
        return self.get_query_with_filters().with_entities(func.sum(DbBet.fee_amount)).scalar()

    def total_amount_avg(self):
        # this should take into account any filters/search inplace
        return (self.total_amount() or 0) // (self.get_query_with_filters().count() or 1)

    def total_paid_amount_avg(self):
        # this should take into account any filters/search inplace
        return (self.total_paid_amount() or 0) // (self.get_query_with_filters().count() or 1)

    def total_fee_amount_avg(self):
        # this should take into account any filters/search inplace
        return (self.total_fee_amount() or 0) // (self.get_query_with_filters().count() or 1)

    def render(self, template, **kwargs):
        # we are only interested in the summary_list page
        if template == 'admin/model/summary_list.html':
            # append a summary_data dictionary into kwargs
            # The title attribute value appears in the actions column
            # all other attributes correspond to their respective Flask-Admin 'column_list' definition
            _current_page = kwargs['page']
            kwargs['summary_data'] = [
                {'title': 'Total', 'name': None, 'amount': amount_formatter(self.total_amount()),
                 'fee_amount': amount_formatter(self.total_fee_amount()),
                 'paid_amount': amount_formatter(self.total_paid_amount())},
                {'title': 'Average', 'name': None, 'amount': amount_formatter(self.total_amount_avg()),
                 'fee_amount': amount_formatter(self.total_fee_amount_avg()),
                 'paid_amount': amount_formatter(self.total_paid_amount_avg())},
            ]
        return super().render(template, **kwargs)


class HomeStatsView(AdminIndexView):
    @expose()
    def index(self):
        network_id = int(request.args.get('network_id', 1))
        W3 = Web3(WebsocketProvider(settings.NETWORKS[network_id].NODE_URL))
        eth_contract_data = settings.NETWORKS[network_id].ETH_CONTRACT
        usdt_contract_data = settings.NETWORKS[network_id].USDT_CONTRACT
        # eth_contract_data.ADDRESS
        with open(usdt_contract_data['abi'], 'r') as f:
            usdt_abi = json.dumps(json.loads(f.read()))
        with open(eth_contract_data['abi'], 'r') as f:
            eth_abi = json.dumps(json.loads(f.read()))
        with open(settings.NETWORKS[network_id].ERC20_CONTRACT['abi'], 'r') as f:
            erc20_abi = json.dumps(json.loads(f.read()))
        eth_balance = W3.eth.getBalance(eth_contract_data.ADDRESS)
        erc_20_contract = W3.eth.contract(Web3.toChecksumAddress(settings.NETWORKS[network_id].ERC20_CONTRACT.ADDRESS),
                                          abi=json.loads(erc20_abi))
        usdt_balance = erc_20_contract.functions.balanceOf(usdt_contract_data.ADDRESS).call()*10**12
        return self.render(self._template, db_models=db_models, func=func, amount_formatter=amount_formatter,
                           Currency=Currency, BetResult=BetResult,
                           usdt_abi=usdt_abi,
                           eth_abi=eth_abi,
                           erc20_abi=erc20_abi,
                           eth_balance=amount_formatter(eth_balance),
                           usdt_balance=amount_formatter(usdt_balance),
                           erc20_address=settings.NETWORKS[network_id].ERC20_CONTRACT.ADDRESS,
                           eth_address=eth_contract_data.ADDRESS,
                           usdt_address=usdt_contract_data.ADDRESS)

    def is_visible(self):
        return False


class ChainEventView(ModelView):
    column_searchable_list = ['user_address']
    can_edit = False
    can_create = False
    column_labels = {'user_address': 'User Address'}
    can_delete = False
    can_view_details = True
    column_list = ['user', 'name', 'amount', 'currency', 'network_id', 'block', 'created']
    column_filters = ['user_address', 'name', 'amount', 'currency', 'network_id', 'block', 'created']
    column_formatters = {
        'created': lambda v, c, m, p: m.created.strftime("%Y/%m/%d %H:%M:%S"),
        'amount': lambda v, c, m, p: amount_formatter(m.amount),
        'data': lambda v, c, m, p: Markup(f"<pre>{pformat(m.data)}</pre>")
    }
    column_default_sort = ('created', True)


class WithdrawView(ModelView):
    column_labels = {'user_address': 'User Address'}
    column_searchable_list = ['user_address']
    fast_mass_delete = False
    action_disallowed_list = ['delete']
    can_delete = False
    can_view_details = True
    can_edit = True
    column_exclude_list = ['withdraw_request_signature']
    column_default_sort = ('created', True)
    column_formatters = {
        'amount': lambda v, c, m, p: amount_formatter(m.amount),
        'actions': lambda v, c, m, p: WithdrawView.get_actions_markup(m),
        'created': lambda v, c, m, p: m.created.strftime("%Y/%m/%d %H:%M:%S"),
    }
    column_filters = ['currency', 'user_address', 'status', 'network_id', 'created']
    column_list = ['user', 'amount', 'currency', 'status', 'network_id', 'created', 'actions']

    def render(self, template, **kwargs):
        self.extra_js = [url_for("static", filename="request_signing.js")]
        return super().render(template, **kwargs)

    @staticmethod
    def get_actions_markup(model):
        divider = 10 ** 12
        approve_form = f"""
            <form method='post' action='{url_for("approve")}'>
                <input type="hidden" name="id" value="{model.id}">
                <input type="hidden" name="redirect_uri" value="{request.url}">
                <input type="hidden" name="user_address" value="" class="user_address">
                <input type="hidden" name="signature" class="signature" value="">
                <input 
                    type="button" 
                    value="Approve ✅" 
                    onclick="withdraw_sign_and_submit(this,'{w3.soliditySha3(
            ['address', 'uint256', 'uint256'],
            [model.user_address,
             int(model.amount) if model.currency == Currency.ETH else int(model.amount // divider),
             model.session_id]).hex()}')" 
                    style="width: 100%; float: left"
                >
            </form>
        """
        reject_form = f"""
            <form method='post' action='{url_for("reject")}'>
                <input type="hidden" name="id" value="{model.id}">
                <input type="hidden" name="redirect_uri" value="{request.url}">
                <input type="text" name="reject_message" style="width: 50%; float: left">
                <input type="submit" value="Reject ❌" style="width: 50%; float: left">
            </form>
        """
        html = ""
        if model.status == WithdrawStatus.PENDING:
            html += approve_form
        if model.status == WithdrawStatus.PENDING or model.status == WithdrawStatus.APPROVED:
            html += reject_form
        return Markup(html)


class AppSettingsView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False

    def get_one(self, id):
        return self.session.query(self.model).get(id)

    @expose('/', methods=['POST', 'GET'])
    def index_view(self):
        app_settings = AppSettings().instance
        request.args = ImmutableMultiDict({'id': app_settings.id})
        return self.edit_view()
