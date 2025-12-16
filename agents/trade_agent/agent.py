from longport.openapi import Config, TradeContext, QuoteContext

config = Config.from_env()

ctx = TradeContext(config)
# ctx = QuoteContext(config)



resp = ctx.account_balance()
# resp = ctx.quote(["NVDA.US"])
print(resp)