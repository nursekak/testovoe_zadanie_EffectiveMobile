# Тестовое задание — EffectiveMobile

Backend-приложение с кастомной системой аутентификации и авторизации на основе JWT и RBAC (Role-Based Access Control).

---

## Стек технологий

| Компонент | Версия |
|---|---|
| Python | 3.11+ |
| Django | 5.0.4 |
| Django REST Framework | 3.15.1 |
| drf-spectacular (Swagger) | 0.27.2 |
| PostgreSQL | 14+ (тестировалось на 18) |
| PyJWT | 2.8.0 |
| argon2-cffi | 23.1.0 |

---

## Структура репозитория

```
testovoe_zadanie_EffectiveMobile/
├── backend/          # Django-приложение
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── create_db.py  # скрипт создания БД
│   ├── config/       # настройки, маршруты
│   └── apps/
│       ├── users/           # модель пользователя
│       ├── authentication/  # JWT, login/logout/refresh
│       ├── access_control/  # RBAC: роли, права, admin API
│       └── business/        # mock бизнес-объекты
└── frontend/
    └── index.html    # SPA-интерфейс (Vanilla JS, без сборки)
```

---

## Быстрый старт

### 1. Виртуальное окружение и зависимости

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Конфигурация

```bash
cp .env.example .env
```

Отредактируйте `.env`:

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

### 3. База данных

```bash
# Автоматически создаст БД через psycopg2:
python create_db.py

# Применить миграции:
python manage.py migrate

# Загрузить тестовые данные (роли, права, пользователи):
python manage.py seed_data
```

### 4. Запуск

```bash
python manage.py runserver
```

Сервер запустится на `http://127.0.0.1:8000`.

---

## Интерфейсы

| URL | Описание |
|---|---|
| `http://127.0.0.1:8000/` | Веб-интерфейс (SPA) |
| `http://127.0.0.1:8000/api/docs/` | Swagger UI |
| `http://127.0.0.1:8000/api/redoc/` | ReDoc |

---

## Тестовые пользователи

| Email | Пароль | Роль |
|---|---|---|
| admin@example.com | Test1234! | admin |
| manager@example.com | Test1234! | manager |
| viewer@example.com | Test1234! | viewer |

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

Refresh-токен никогда не хранится в открытом виде — только его SHA-256 хэш. При logout или ротации токен помечается `revoked=True`.

### access_control_role — Роли

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(64) UNIQUE | Название: admin, manager, viewer |
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

```
Пользователь → [UserRole] → Роль → [RolePermission] → Право (resource:action)
```

**Логика проверки запроса:**

1. DRF-аутентификатор читает заголовок `Authorization: Bearer <access_token>`
2. Токен валидируется через PyJWT (`HS256`, проверка `exp` и `type`)
3. Из payload извлекается `sub` (UUID пользователя)
4. Пользователь загружается из БД (только если `is_active=True`)
5. Декоратор `@require_permission(resource, action)` проверяет наличие нужного права через JOIN: `UserRole → Role → RolePermission → Permission`
6. При отсутствии аутентификации — `401 Unauthorized`
7. При отсутствии нужного права — `403 Forbidden`

**Матрица прав:**

| Роль | Права |
|---|---|
| admin | document:*, report:*, application:*, admin:access |
| manager | document:read/create/update, report:read/create, application:read/create/update |
| viewer | document:read, report:read, application:read |

---

## API Endpoints

### Аутентификация `/api/auth/`

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход (email + пароль) |
| POST | `/api/auth/refresh/` | Обновление access-токена |
| POST | `/api/auth/logout/` | Выход (отзыв refresh-токена) |

### Профиль `/api/users/`

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/users/me/` | Получить профиль |
| PATCH | `/api/users/me/` | Обновить профиль |
| DELETE | `/api/users/me/` | Мягкое удаление аккаунта + logout |

### Администрирование `/api/admin/`

Все эндпоинты требуют право `admin:access`.

| Метод | URL | Описание |
|---|---|---|
| GET/POST | `/api/admin/roles/` | Список / создание ролей |
| GET/PATCH/DELETE | `/api/admin/roles/{id}/` | Операции с ролью |
| GET/POST | `/api/admin/roles/{id}/permissions/` | Права роли / добавить |
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

## Как работают токены

- **Access-токен** — JWT (HS256), содержит `sub` (user UUID), `email`, `exp`, `type=access`. TTL: `JWT_ACCESS_TTL_MINUTES` минут (по умолчанию 15).
- **Refresh-токен** — случайная 64-символьная hex-строка. В БД хранится только её SHA-256 хэш. TTL: `JWT_REFRESH_TTL_DAYS` дней (по умолчанию 30).
- При `POST /api/auth/refresh/` старый refresh-токен отзывается и выдаётся новая пара (ротация токенов).
- При `DELETE /api/users/me/` пользователь мягко удаляется (`is_active=False`) и все его активные refresh-токены отзываются.
