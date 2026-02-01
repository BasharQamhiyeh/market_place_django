from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

USERS = [
    {"phone": "0767008265", "password": "bashar123"},
    {"phone": "0799086132", "password": "yazan123"},
    {"phone": "0547222366", "password": "motasem123"},
]

class Command(BaseCommand):
    def handle(self, *args, **options):
        for u in USERS:
            if not User.objects.filter(phone=u["phone"]).exists():
                User.objects.create_superuser(
                    phone=u["phone"],
                    password=u["password"],
                )
