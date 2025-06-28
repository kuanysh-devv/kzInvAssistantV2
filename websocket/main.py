from django.core.cache import cache
from sanic import Sanic
from sanic_ext import Extend
import json

from helpers import assistant_exists, get_assistants, get_assistant_name_by_id
from ask import ask_assistant_ws

app = Sanic("WebSocketAssistant")
Extend(app)


@app.websocket("/ws/assistant")
async def handle_assistant_ws(request, ws):
    user_id = id(ws)
    username = f"user_{user_id}"

    try:
        async for message in ws:
            try:
                data = json.loads(message)
                type_ = data.get("type")

                if type_ in "select_assistant":
                    selected_assistant_id = data.get("assistant_id")
                    if not await assistant_exists(selected_assistant_id):
                        await ws.send(json.dumps({
                            "type": "error",
                            "message": "Ассистент не найден"
                        }))
                        continue

                    assistant_name = await get_assistant_name_by_id(selected_assistant_id)
                    cache.set(f"user_assistant:{user_id}", selected_assistant_id, timeout=3600)

                    await ws.send(json.dumps({
                        "type": "success",
                        "message": f"Ассистент выбран: {assistant_name}"
                    }))

                elif type_ == "get_assistants":
                    assistants = await get_assistants()
                    await ws.send(json.dumps({
                        "type": "assistant_list",
                        "assistants": assistants
                    }))

                elif type_ == "question":
                    question = data.get("question")
                    if not question:
                        await ws.send(json.dumps({
                            "type": "error",
                            "message": "Пустой вопрос"
                        }))
                        continue

                    try:
                        answer = await ask_assistant_ws(question, user_id, username)
                        await ws.send(json.dumps({
                            "type": "answer",
                            "message": answer
                        }))
                    except Exception as e:
                        await ws.send(json.dumps({
                            "type": "error",
                            "message": str(e)
                        }))

            except Exception as e:
                await ws.send(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    finally:
        cache.delete(f"user_assistant:{user_id}")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
