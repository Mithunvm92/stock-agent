from kiteconnect import KiteConnect
import os


class ZerodhaBroker:

    def __init__(self):

        self.api_key = os.getenv(
            "yy5no3jj0ynnc49f"
        )

        self.access_token = os.getenv(
            "ZERODHA_ACCESS_TOKEN"
        )

        self.kite = KiteConnect(
            api_key=self.api_key
        )

        self.kite.set_access_token(
            self.access_token
        )

    def place_market_order(
        self,
        symbol,
        transaction_type,
        quantity
    ):

        try:

            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,

                exchange=self.kite.EXCHANGE_NSE,

                tradingsymbol=symbol.replace(
                    '.NS',
                    ''
                ),

                transaction_type=transaction_type,

                quantity=quantity,

                product=self.kite.PRODUCT_MIS,

                order_type=self.kite.ORDER_TYPE_MARKET,

                validity=self.kite.VALIDITY_DAY
            )

            print(
                f"✅ Zerodha Order Placed: "
                f"{order_id}"
            )

            return order_id

        except Exception as e:

            print(
                f"❌ Zerodha Order Failed: {e}"
            )

            return None
