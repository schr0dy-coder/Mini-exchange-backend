import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class OrderBookConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbol = None
        self.room_group_name = None

    async def connect(self):
        query = self.scope.get("query_string", b"").decode()
        self.symbol = None
        for part in query.split("&"):
            if part.startswith("symbol="):
                self.symbol = part.split("=", 1)[1].strip()
                break
        if not self.symbol:
            await self.close()
            return
        self.room_group_name = f"orderbook_{self.symbol}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        from .services.orderbook import get_order_book
        book = await sync_to_async(get_order_book)(self.symbol)
        await self.send(text_data=json.dumps(book, default=str))

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def orderbook_update(self, event):
        await self.send(text_data=json.dumps(event["data"], default=str))

class PricesConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = "prices_stream"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def prices_update(self, event):
        await self.send(text_data=json.dumps(event["data"], default=str))
