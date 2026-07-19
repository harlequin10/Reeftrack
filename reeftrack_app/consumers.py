import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AssessmentSyncConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time assessment sync.

    All authenticated users join the 'assessments' group.
    When any assessment changes, a 'refresh' signal is pushed
    to all connected clients. The client then fetches fresh
    data via the /api/assessments/sync/ HTTP endpoint.
    """

    async def connect(self):
        self.user = self.scope.get('user')
        if self.user and self.user.is_authenticated:
            self.group_name = 'assessments'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        pass

    async def assessment_refresh(self, event):
        """Handle refresh signal from the channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'refresh',
            'action': event.get('action', ''),
        }))
