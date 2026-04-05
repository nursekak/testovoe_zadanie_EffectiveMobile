"""
Management command: python manage.py seed_data

Создаёт тестовые роли, права и пользователей для демонстрации системы.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.access_control.models import Role, Permission, RolePermission, UserRole

User = get_user_model()

PERMISSIONS_MAP = {
    "document": ["read", "create", "update", "delete"],
    "report":   ["read", "create"],
    "application": ["read", "create", "update"],
    "admin":    ["access"],
}

ROLES_PERMISSIONS = {
    "admin": [
        ("document", "read"), ("document", "create"), ("document", "update"), ("document", "delete"),
        ("report", "read"), ("report", "create"),
        ("application", "read"), ("application", "create"), ("application", "update"),
        ("admin", "access"),
    ],
    "manager": [
        ("document", "read"), ("document", "create"), ("document", "update"),
        ("report", "read"), ("report", "create"),
        ("application", "read"), ("application", "create"), ("application", "update"),
    ],
    "viewer": [
        ("document", "read"),
        ("report", "read"),
        ("application", "read"),
    ],
}

USERS = [
    {
        "email": "admin@example.com",
        "password": "Test1234!",
        "first_name": "Александр",
        "last_name": "Иванов",
        "middle_name": "Петрович",
        "role": "admin",
    },
    {
        "email": "manager@example.com",
        "password": "Test1234!",
        "first_name": "Мария",
        "last_name": "Петрова",
        "middle_name": "Сергеевна",
        "role": "manager",
    },
    {
        "email": "viewer@example.com",
        "password": "Test1234!",
        "first_name": "Кирилл",
        "last_name": "Сидоров",
        "middle_name": "",
        "role": "viewer",
    },
]


class Command(BaseCommand):
    help = "Заполнить БД тестовыми ролями, правами и пользователями"

    def handle(self, *args, **options):
        self.stdout.write("=== Seed data ===")

        perm_objects = {}
        for resource, actions in PERMISSIONS_MAP.items():
            for action in actions:
                perm, created = Permission.objects.get_or_create(resource=resource, action=action)
                perm_objects[(resource, action)] = perm
                tag = "создано" if created else "уже есть"
                self.stdout.write(f"  Право {resource}:{action} — {tag}")

        role_objects = {}
        for role_name, perm_list in ROLES_PERMISSIONS.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={"description": f"Роль: {role_name}"},
            )
            role_objects[role_name] = role
            tag = "создана" if created else "уже есть"
            self.stdout.write(f"  Роль '{role_name}' — {tag}")

            for resource, action in perm_list:
                perm = perm_objects[(resource, action)]
                RolePermission.objects.get_or_create(role=role, permission=perm)

        for raw in USERS:
            role_name = raw["role"]
            password = raw["password"]

            user, created = User.objects.get_or_create(
                email=raw["email"],
                defaults={
                    "first_name": raw["first_name"],
                    "last_name": raw["last_name"],
                    "middle_name": raw.get("middle_name", ""),
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"  Пользователь {user.email} — создан")
            else:
                self.stdout.write(f"  Пользователь {user.email} — уже есть")

            role = role_objects[role_name]
            _, assigned = UserRole.objects.get_or_create(user=user, role=role)
            if assigned:
                self.stdout.write(f"    -> роль '{role_name}' назначена")

        self.stdout.write(self.style.SUCCESS("=== Готово ==="))
