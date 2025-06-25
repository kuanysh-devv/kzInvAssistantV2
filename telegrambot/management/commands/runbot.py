from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Starts the Telegram bot"

    def handle(self, *args, **kwargs):
        from telegrambot.bot import main  # or telebot if renamed
        main()
