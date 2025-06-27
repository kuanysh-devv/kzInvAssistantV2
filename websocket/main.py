import os
import sys
import django
from asgiref.sync import sync_to_async
from django.core.cache import cache

# Step 1: Add base directory (where manage.py is) to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Step 2: Set DJANGO_SETTINGS_MODULE to point to your settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kzInvAssistantV2.settings")

# Step 3: Setup Django
django.setup()

# Now import your Django models
from telegrambot.models import Assistant

# Basic Sanic WebSocket example
from sanic import Sanic
from sanic_ext import Extend
import json

app = Sanic("WebSocketAssistant")
Extend(app)


@sync_to_async
def get_assistants():
    return list(Assistant.objects.values("assistant_id", "name", "description"))


@app.websocket("/ws/assistant")
async def handle_assistant_ws(request, ws):
    user_id = id(ws)  # You can replace with actual session/user ID in production
    print(user_id)
    # Fetch all assistants from DB
    assistants = await get_assistants()

    # Send list of assistants to frontend
    await ws.send(json.dumps({
        "type": "assistant_list",
        "assistants": assistants
    }))

    async for message in ws:
        try:
            data = json.loads(message)
            if data.get("type") == "select_assistant":
                selected_assistant_id = data.get("assistant_id")

                exists = await sync_to_async(Assistant.objects.filter(assistant_id=selected_assistant_id).exists)()

                if not exists:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "❌ Ассистент с таким ID не найден."
                    }))
                    continue

                # Store selection in Redis
                cache.set(f"user_assistant:{user_id}", selected_assistant_id, timeout=3600)

                await ws.send(json.dumps({
                    "type": "confirmation",
                    "message": f"Ассистент выбран: {exists.name}"
                }))

        except Exception as e:
            await ws.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
