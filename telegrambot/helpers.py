from __future__ import annotations
from websocket.helpers import get_assistants, log_interaction
import asyncio
from websocket.ask import get_question_cache_key, get_user_thread, set_user_thread, get_selected_object_id
from aiogram.enums import ChatAction
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from openai import OpenAI
import os
from django.core.cache import cache

load_dotenv()


# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    project=os.getenv('PROJECT_ID'),
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def send_assistant_menu(event: Message | CallbackQuery):
    assistants = await get_assistants()
    keyboard = InlineKeyboardBuilder()
    for assistant in assistants:
        keyboard.button(text=assistant["name"], callback_data=str(assistant["id"]))
    keyboard.adjust(1)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            "Выберите ассистента для начала работы:",
            reply_markup=keyboard.as_markup()
        )
    elif isinstance(event, Message):
        await event.answer(
            "Выберите ассистента для начала работы:",
            reply_markup=keyboard.as_markup()
        )



async def ask_assistant_bot(question: str, user_id: int, username: str, message: Message):
    """
    Handles user question by sending it to the assistant and returning annotated answer.
    """
    selected_assistant_id = await get_selected_object_id(user_id)
    if not selected_assistant_id:
        await send_assistant_menu(message)
        return

    cache_key = get_question_cache_key(selected_assistant_id, question)
    cached_answer = cache.get(cache_key)
    if cached_answer:
        print("[CACHE HIT - Telegram bot]")
        await message.answer(cached_answer)
        return

    # Get or create the user's thread
    thread_id = get_user_thread(user_id)
    if not thread_id:
        thread = await asyncio.to_thread(client.beta.threads.create)
        thread_id = thread.id
        set_user_thread(user_id, thread_id)
    else:
        thread = await asyncio.to_thread(client.beta.threads.retrieve, thread_id)

    # Create initial user message
    await asyncio.to_thread(
        client.beta.threads.messages.create,
        thread_id=thread_id,
        role="user",
        content=question
    )

    print(f"[{username}] Question: {question}")

    # Wait for any existing run to finish (polling loop)
    while True:
        runs = await asyncio.to_thread(client.beta.threads.runs.list, thread_id=thread_id)
        active_run = next((r for r in runs.data if r.status == "active"), None)

        if active_run:
            await message.answer_chat_action(action=ChatAction.TYPING)
            await asyncio.sleep(2)
        else:
            break

    # Create and poll the run
    run = await asyncio.to_thread(
        client.beta.threads.runs.create_and_poll,
        thread_id=thread_id,
        assistant_id=selected_assistant_id
    )

    if run.status != "completed":
        raise Exception("Произошла ошибка. Попробуйте еще раз.")

    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            messages_page = await asyncio.to_thread(
                client.beta.threads.messages.list, thread_id=thread_id
            )

            assistant_messages = [
                m for m in messages_page.data if m.role == "assistant"
            ]
            if not assistant_messages:
                raise Exception("No assistant response found.")

            last_message = assistant_messages[0]
            content_block = last_message.content[0].text
            message_text = content_block.value
            annotations = content_block.annotations

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

            if not final_message.strip().startswith("К сожалению"):
                cache.set(cache_key, final_message, timeout=600)

            await log_interaction(username, question, final_message)
            yield final_message
            return

        except Exception as e:
            retries += 1
            print(f"[Retry {retries}/{max_retries}] Error: {e}")
            if retries < max_retries:
                await asyncio.sleep(2 ** retries)
            else:
                raise Exception("Maximum retry attempts reached.") from e


def process_annotations(annotations_list):
    """
    Process annotations to group them by text and prepare citations.
    Returns a tuple of the updated message content and formatted citations.
    """
    citations = {}
    message_content_value = annotations_list[0].message.content.value

    for index, annotation in enumerate(annotations_list):
        annotation_text = annotation.text
        if annotation_text not in citations:
            citations[annotation_text] = []
        citations[annotation_text].append(index + 1)

        # Replace annotation text with placeholder for later citation
        message_content_value = message_content_value.replace(annotation_text, f' [{index + 1}]')

    # Prepare citation format for repeated annotations
    formatted_citations = [
        f"{''.join([f'[{i}]' for i in indices])} {text}" for text, indices in citations.items()
    ]

    return message_content_value, formatted_citations