import asyncio
import hashlib
import os
from typing import Any

from openai import OpenAI
from django.core.cache import cache
from asgiref.sync import sync_to_async

from websocket.helpers import log_interaction, get_assistant_id_by_object_id

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("PROJECT_ID"),
)

def get_user_thread(user_id: int) -> str | None:
    return cache.get(f"user_thread:{user_id}")

def set_user_thread(user_id: int, thread_id: str, ttl: int = 3600):
    cache.set(f"user_thread:{user_id}", thread_id, timeout=ttl)

def delete_user_thread(user_id: int):
    cache.delete(f"user_thread:{user_id}")

def get_question_cache_key(assistant_id: str, question: str) -> str:
    # Create a stable hash to avoid long cache keys
    question_hash = hashlib.sha256(question.strip().lower().encode()).hexdigest()
    return f"assistant_response:{assistant_id}:{question_hash}"


@sync_to_async
def get_selected_object_id(user_id):
    return cache.get(f"user_assistant:{user_id}")


async def ask_assistant_ws(question: str, user_id: int, username: str) -> Any | None:
    object_id = await get_selected_object_id(user_id)
    if not object_id:
        raise Exception("Ассистент не выбран.")

    selected_assistant_id = await get_assistant_id_by_object_id(object_id)
    # Check if the question is cached for this assistant
    cache_key = get_question_cache_key(selected_assistant_id, question)
    cached_answer = cache.get(cache_key)
    if cached_answer:
        print("[CACHE HIT]")
        return cached_answer

    # Get or create thread
    thread_id = get_user_thread(user_id)
    if not thread_id:
        thread = await asyncio.to_thread(client.beta.threads.create)
        thread_id = thread.id
        set_user_thread(user_id, thread_id)
    else:
        thread = await asyncio.to_thread(client.beta.threads.retrieve, thread_id)

    # Send user question
    await asyncio.to_thread(
        client.beta.threads.messages.create,
        thread_id=thread_id,
        role="user",
        content=question
    )

    print(f"[{username}] Question: {question}")

    # Poll until no active run
    while True:
        runs = await asyncio.to_thread(client.beta.threads.runs.list, thread_id=thread_id)
        active_run = next((r for r in runs.data if r.status == "active"), None)
        if active_run:
            await asyncio.sleep(2)
        else:
            break

    # Create new run
    run = await asyncio.to_thread(
        client.beta.threads.runs.create_and_poll,
        thread_id=thread_id,
        assistant_id=selected_assistant_id
    )

    if run.status != "completed":
        raise Exception("Ассистент не дал ответа. Попробуйте еще раз.")

    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            messages_page = await asyncio.to_thread(
                client.beta.threads.messages.list, thread_id=thread_id
            )

            assistant_messages = [m for m in messages_page.data if m.role == "assistant"]
            if not assistant_messages:
                raise Exception("Нет ответа от ассистента.")

            last_message = assistant_messages[0]
            content_block = last_message.content[0].text
            message_text = content_block.value
            annotations = content_block.annotations

            # Process citations
            citations = {}
            for idx, annotation in enumerate(annotations):
                text = annotation.text
                citations.setdefault(text, []).append(idx + 1)
                message_text = message_text.replace(text, f' [{idx + 1}]')

            formatted_citations = [
                f"{''.join(f'[{i}]' for i in indices)} {text}"
                for text, indices in citations.items()
            ]

            final_message = message_text + "\n\n" + "\n".join(formatted_citations)

            # Cache only if answer is not a fallback message
            if not final_message.strip().startswith("К сожалению"):
                cache.set(cache_key, final_message, timeout=6)

            await log_interaction(username, question, final_message)
            return final_message

        except Exception as e:
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(2 ** retries)
            else:
                raise Exception("Произошла ошибка при получении ответа.") from e
    return None