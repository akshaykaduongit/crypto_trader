from binance.enums import *
from binance.client import Client
from Binance import BinancePrivate

api_key = "THMrraVxI5cD8FYtbrJcfged6URzbJRujMH9zkN88mqHc3bQDlAsbuUZAAbxxK2d"
api_secret = "LkVaa9AA1SO3RuoZdcYCiaWCiq90cOeojg4VQOwxt23t6cMC2OCCw5M51uwr6XbU"

client = Client(api_key, api_secret)


#order = client.order_market_buy(    symbol='ADAEUR',    quantity=10)
#print("Type:{}".format(type(order)))
#print("Order response:{}".format(order))


#order = client.order_market_sell(    symbol='ADAEUR',    quantity=10)
#print("Type:{}".format(type(order)))
#print("Order response:{}".format(order))
#order = order = client.order_limit_sell(    symbol='ADAEUR',    quantity=10,    price=1.16632);

bp = BinancePrivate()
#order = bp.order_market_buy('ADAEUR','10');
order = bp.order_market_sell('ADAEUR','10');
print("Order dictionary:{}".format(order))
print("Average buy price:{}".format(order["average_price"]))
