# Backend: Custom Auth & Authorization

Backend-приложение на Django REST Framework с кастомной JWT-аутентификацией и ролевой системой разграничения прав доступа (RBAC).

---

## Стек технологий

| Компонент | Версия |
|---|---|
| Python | 3.11+ |
| Django | 5.0.4 |
| Django REST Framework | 3.15.1 |
| PostgreSQL | 14+ |
| PyJWT | 2.8.0 |
| argon2-cffi | 23.1.0 |

---

## Быстрый старт

```bash
# 1. Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скопировать файл конфигурации и заполнить переменные
cp .env.example .env

# 4. Создать базу данных PostgreSQL
#    psql -U postgres -c "CREATE DATABASE auth_db;"

# 5. Применить миграции
python manage.py migrate

# 6. Заполнить тестовыми данными
python manage.py seed_data

# 7. Запустить сервер
python manage.py runserver
```

---

## Конфигурация (.env)

```
SECRET_KEY=<длинная-случайная-строка>
DEBUG=True
DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=30
```

---

## Схема базы данных

### users_user — Пользователи

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | Первичный ключ |
| email | VARCHAR UNIQUE | Адрес электронной почты (логин) |
| password | VARCHAR | Хэш пароля (Argon2) |
| first_name | VARCHAR(150) | Имя |
| last_name | VARCHAR(150) | Фамилия |
| middle_name | VARCHAR(150) NULL | Отчество |
| is_active | BOOLEAN | `False` — мягко удалённый пользователь |
| is_staff | BOOLEAN | Технический флаг суперпользователя |
| created_at | TIMESTAMPTZ | Дата регистрации |
| updated_at | TIMESTAMPTZ | Дата последнего обновления |

### authentication_refreshtoken — Refresh-токены

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| user | FK → users_user | Владелец токена |
| token_hash | VARCHAR(64) | SHA-256 хэш raw-токена |
| expires_at | TIMESTAMPTZ | Срок действия |
| revoked | BOOLEAN | `True` — токен отозван (logout) |
| created_at | TIMESTAMPTZ | |

Refresh-токен никогда не хранится в открытом виде — только его SHA-256 хэш. При logout/ротации токен помечается `revoked=True`.

### access_control_role — Роли

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(64) UNIQUE | Название роли: admin, manager, viewer |
| description | TEXT | Описание |

### access_control_permission — Права доступа

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| resource | VARCHAR(64) | Ресурс: document, report, application, admin |
| action | VARCHAR(32) | Действие: read, create, update, delete, access |
| UNIQUE(resource, action) | | |

### access_control_rolepermission — Связь ролей и прав

| Поле | Тип |
|---|---|
| role | FK → Role |
| permission | FK → Permission |

### access_control_userrole — Связь пользователей и ролей

| Поле | Тип |
|---|---|
| user | FK → User |
| role | FK → Role |

---

## Система разграничения прав доступа (RBAC)

Используется модель **Role-Based Access Control**:

```
Пользователь → [UserRole] → Роль → [RolePermission] → Право (resource:action)
```

**Логика проверки запроса:**

1. Middleware читает заголовок `Authorization: Bearer <access_token>`
2. Токен валидируется через PyJWT (`HS256`, проверка `exp` и `type`)
3. Из payload извлекается `sub` (UUID пользователя)
4. Пользователь загружается из БД (только если `is_active=True`)
5. Декоратор `@require_permission(resource, action)` проверяет наличие нужного права через JOIN: `UserRole → Role → RolePermission → Permission`
6. При отсутствии аутентификации — `401 Unauthorized`
7. При отсутствии нужного права — `403 Forbidden`

**Тестовые роли и права:**

| Роль | Права |
|---|---|
| admin | document:*, report:*, application:*, admin:access |
| manager | document:read/create/update, report:read/create, application:read/create/update |
| viewer | document:read, report:read, application:read |

**Тестовые пользователи:**

| Email | Пароль | Роль |
|---|---|---|
| admin@example.com | Test1234! | admin |
| manager@example.com | Test1234! | manager |
| viewer@example.com | Test1234! | viewer |

---

## API Endpoints

### Аутентификация `/api/auth/`

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход (email + пароль) |
| POST | `/api/auth/refresh/` | Обновление access-токена |
| POST | `/api/auth/logout/` | Выход (отзыв refresh-токена) |

**Пример регистрации:**
```json
POST /api/auth/register/
{
  "email": "user@example.com",
  "password": "MyPass123!",
  "password_confirm": "MyPass123!",
  "first_name": "Иван",
  "last_name": "Иванов",
  "middle_name": "Иванович"
}
```

**Пример входа:**
```json
POST /api/auth/login/
{
  "email": "admin@example.com",
  "password": "Test1234!"
}
```

**Ответ:**
```json
{
  "user": { "id": "...", "email": "admin@example.com", ... },
  "access_token": "<jwt>",
  "refresh_token": "<hex-string>"
}
```

### Профиль пользователя `/api/users/`

| Метод | URL | Описание | Права |
|---|---|---|---|
| GET | `/api/users/me/` | Получить профиль | аутентификация |
| PATCH | `/api/users/me/` | Обновить профиль | аутентификация |
| DELETE | `/api/users/me/` | Мягкое удаление аккаунта | аутентификация |

### Администрирование `/api/admin/`

Все эндпоинты требуют роль `admin` (право `admin:access`).

| Метод | URL | Описание |
|---|---|---|
| GET/POST | `/api/admin/roles/` | Список / создание ролей |
| GET/PATCH/DELETE | `/api/admin/roles/{id}/` | Операции с ролью |
| GET/POST | `/api/admin/roles/{id}/permissions/` | Права роли / добавить право |
| DELETE | `/api/admin/roles/{id}/permissions/{perm_id}/` | Убрать право у роли |
| GET/POST | `/api/admin/permissions/` | Список / создание прав |
| GET/PATCH/DELETE | `/api/admin/permissions/{id}/` | Операции с правом |
| GET/POST | `/api/admin/users/{id}/roles/` | Роли пользователя / назначить |
| DELETE | `/api/admin/users/{id}/roles/{role_id}/` | Убрать роль у пользователя |

### Бизнес-объекты `/api/business/`

| Метод | URL | Требуемое право |
|---|---|---|
| GET | `/api/business/documents/` | document:read |
| POST | `/api/business/documents/` | document:create |
| GET | `/api/business/reports/` | report:read |
| POST | `/api/business/reports/` | report:create |
| GET | `/api/business/applications/` | application:read |
| POST | `/api/business/applications/` | application:create |

---

## Аутентификация: как работают токены

- **Access-токен** — JWT (HS256), содержит `sub` (user UUID), `email`, `exp`, `type=access`. Живёт `JWT_ACCESS_TTL_MINUTES` минут.
- **Refresh-токен** — случайная 64-символьная hex-строка. В БД хранится только её SHA-256 хэш. Живёт `JWT_REFRESH_TTL_DAYS` дней.
- При `POST /refresh/` старый refresh-токен отзывается, выдаётся новая пара (ротация).
- При `DELETE /users/me/` все активные refresh-токены пользователя отзываются.

---

## Структура проекта

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── fixtures/
│   └── seed_description.json
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── users/
    │   ├── models.py          # CustomUser
    │   ├── serializers.py
    │   ├── views.py           # GET/PATCH/DELETE /me/
    │   ├── urls.py
    │   └── management/commands/seed_data.py
    ├── authentication/
    │   ├── models.py          # RefreshToken
    │   ├── services.py        # JWT: generate/validate/revoke
    │   ├── middleware.py      # JWTAuthMiddleware
    │   ├── serializers.py
    │   ├── views.py           # register/login/refresh/logout
    │   ├── urls.py
    │   └── utils.py           # @require_authenticated
    ├── access_control/
    │   ├── models.py          # Role, Permission, RolePermission, UserRole
    │   ├── decorators.py      # @require_permission, @require_admin
    │   ├── serializers.py
    │   ├── views.py           # Admin API
    │   └── urls.py
    └── business/
        ├── views.py           # Mock: documents, reports, applications
        └── urls.py
```
