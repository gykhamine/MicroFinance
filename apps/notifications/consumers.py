import json
from channels.generic.websocket import AsyncWebsocketConsumer
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close(); return
        self.room = f"notif_{self.scope['user'].pk}"
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()
    async def disconnect(self, code):
        if hasattr(self,'room'):
            await self.channel_layer.group_discard(self.room, self.channel_name)
    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))
