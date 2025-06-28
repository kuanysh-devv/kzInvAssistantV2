# websocket/db_helpers.py

import os
import sys
import django
from asgiref.sync import sync_to_async

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kzInvAssistantV2.settings")
django.setup()

# Now you can safely import models
from telegrambot.models import Assistant, InteractionLog


@sync_to_async
def get_assistants():
    return list(Assistant.objects.values("id", "name", "description"))


@sync_to_async
def assistant_exists(object_id: str) -> bool:
    return Assistant.objects.filter(id=object_id).exists()


@sync_to_async
def get_assistant_name_by_id(object_id):
    assistant = Assistant.objects.filter(id=object_id).first()
    return assistant.name if assistant else None

@sync_to_async
def get_assistant_id_by_object_id(object_id):
    assistant = Assistant.objects.filter(id=object_id).first()
    return assistant.assistant_id if assistant else None


@sync_to_async
def log_interaction(username, question, answer):
    InteractionLog.objects.create(
        username=username,
        question=question,
        answer=answer
    )
