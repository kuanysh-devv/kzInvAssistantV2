from __future__ import annotations
import asyncio
from aiogram.methods import SendChatAction
from django.core.cache import cache
from telegram.constants import ChatAction
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from websocket.ask import get_user_thread, set_user_thread
from websocket.helpers import (get_assistant_id_by_object_id, get_assistant_desc_by_object_id,
                               get_assistant_name_by_id)
from .helpers import (ask_assistant_bot, client, send_assistant_menu)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
router = Router()
dp = Dispatcher()
dp.include_router(router)


async def get_username(bot: Bot, user_id: int):
    try:
        user = await bot.get_chat(user_id)  # Get user details
        return user.username  # Access the username
    except Exception as e:
        print(e)
        return None



@router.message(Command("start"))
async def start_command_handler(message: Message):
    """
    Handles the /start command, allowing the user to choose an assistant.
    """
    user_id = message.from_user.id

    # 🔁 Use Redis instead of in-memory dict
    thread_id = get_user_thread(user_id)
    if not thread_id:
        thread = await asyncio.to_thread(client.beta.threads.create)
        thread_id = thread.id
        set_user_thread(user_id, thread_id)

    await message.answer(
        "Добро пожаловать в бот компании Kazakh Invest! Вот список доступных команд:\n\n"
        "/start - Начать работу с ботом\n"
        "/change_assistant - Сменить текущего ассистента\n"
    )
    await send_assistant_menu(message)


async def handle_message(message: Message):
    """
    Handles user messages by passing them to the assistant and returning the response.
    """
    question = message.text
    user_id = message.from_user.id  # Unique identifier for the user
    username = await get_username(bot, user_id)
    # Notify the user that their question is being processed
    await bot(SendChatAction(action=ChatAction.TYPING, chat_id=message.chat.id))

    try:
        # Stream responses back to the user
        response_generator = ask_assistant_bot(question, user_id, username, message)
        # Collect responses from the async generator
        async for partial_response in response_generator:
            await message.answer(partial_response, disable_web_page_preview=True)
    except Exception as e:
        # Handle exceptions and notify the user
        await message.answer(f"An error occurred: {str(e)}")


async def handle_assistant_selection(callback_query: CallbackQuery):
    """
    Handles the assistant selection made by the user.
    """
    await callback_query.answer()  # Acknowledge the query

    selected_assistant_id = callback_query.data
    user_id = callback_query.from_user.id

    # Store the selected assistant for the user
    selected_assistant = await get_assistant_id_by_object_id(selected_assistant_id)
    cache.set(f"user_assistant:{user_id}", selected_assistant, timeout=3600)

    # Get assistant details for confirmation
    name = await get_assistant_name_by_id(selected_assistant_id)
    desc = await get_assistant_desc_by_object_id(selected_assistant_id)

    if selected_assistant:
        await callback_query.message.edit_text(
            f"Вы выбрали ассистента: {name}."
            f"\nОписание: {desc}"
            "\nТеперь вы можете задать ваш вопрос."
        )
    else:
        await callback_query.message.edit_text("Произошла ошибка при выборе ассистента. Попробуйте еще раз.")


async def change_assistant(callback_query: CallbackQuery):
    """
    Allows the user to change their selected assistant.
    """
    await send_assistant_menu(callback_query)


def main():
    """
    Main function to run the Telegram bot.
    """
    # Command handlers
    router.message.register(send_assistant_menu, CommandStart())

    router.message(Command("change_assistant"))(change_assistant)

    # Message handlers
    router.message.register(handle_message)

    # Callback query handlers
    router.callback_query()(handle_assistant_selection)

    # Start polling
    import asyncio
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
