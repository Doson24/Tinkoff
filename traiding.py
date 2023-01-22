import os
from tinkoff.invest import CandleInterval, Client, HistoricCandle, RequestError, OrderDirection, OrderType
from datetime import datetime


FIGI = 'TCS00A1039N1'

def run():

    TOKEN = os.environ["TOKEN_test_all"]
    account_id = os.environ['account_id']

    with Client(TOKEN) as client:
        # Открытые ордера или частично исполненные
        # orders = client.orders.get_orders(account_id=account_id).orders
        # print(orders)

        # не исполненные заявки можно отменить
        # order_id = orders[0].order_id
        # print("Lets cancel order w id %s" % order_id)
        # r = client.orders.cancel_order(account_id=account_id, order_id=order_id)
        # print(r)

        # book = client.market_data.get_order_book(figi=FIGI, depth=50)
        # print(book)

        # fast_price_sell, fast_price_buy = book.asks[0], book.bids[0] # центр стакана, мин спред
        # best_price_sell, best_price_buy = book.asks[-1], book.bids[-1]  # края стакана, макс спред
        # print(fast_price_sell, fast_price_buy)
        # print(best_price_sell, best_price_buy)
        #
        # # только для удобной отладки, в проде - лишнее
        # bids = [cast_money(p.price) for p in book.bids] # покупатели
        # asks = [cast_money(p.price) for p in book.asks] # продавцы
        # print(bids, asks, sep="\n")

        # ! также нужно учитывать объемы
        # е. price >= max(asks), а quantity > max(asks).quantity, то заберем из сл глубины,
        # по цене ВЫШЕ чем нам надо !!!
        # см. https://tinkoff.github.io/investAPI/faq_orders/

        # r = client.orders.post_order(
        #     order_id=str(datetime.utcnow().timestamp()),
        #     figi=FIGI,
        #     quantity=1,
        #     account_id=account_id,
        #     direction=OrderDirection.ORDER_DIRECTION_BUY,
        #     order_type=OrderType.ORDER_TYPE_MARKET
        # )

        # Рыночная, без указания цены (по лучшей доступной для объема)
        r = client.orders.post_order(
            order_id=str(datetime.utcnow().timestamp()),
            figi=FIGI,
            quantity=1,
            account_id=account_id,
            direction=OrderDirection.ORDER_DIRECTION_BUY,
            order_type=OrderType.ORDER_TYPE_MARKET
        )

        # Лимитка (ограничения цен - нижние края стакана)
        # r = client.orders.post_order(
        #     order_id=str(datetime.utcnow().timestamp()),
        #     figi=FIGI,
        #     quantity=1,
        #     price=Quotation(units=99, nano=0),
        #     account_id=account_id,
        #     direction=OrderDirection.ORDER_DIRECTION_SELL,
        #     order_type=OrderType.ORDER_TYPE_LIMIT
        # )
        #
        print(r)

        # accounts = client.users.get_accounts()
        # print("\nСписок текущих аккаунтов\n")
        # for account in accounts.accounts:
        #     print("\t", account.id, account.name, account.access_level.name)

run()