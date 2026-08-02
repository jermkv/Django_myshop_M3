# Hop & Barley — Интернет-магазин на Django/DRF

Интернет-магазин для продажи ингредиентов домашнего пивоварения. Построен на Django (веб-интерфейс, сессионная авторизация) и Django REST Framework (REST API с JWT).

---

## Содержание

- [Описание](#описание)
- [Установка и запуск через Docker](#установка-и-запуск-через-docker)
- [JWT и примеры API](#jwt-и-примеры-api)
- [Запуск тестов и линтеров](#запуск-тестов-и-линтеров)
- [Структура проекта](#структура-проекта)

---

## Описание

**Hop & Barley** — полноценный интернет-магазин с:

- Каталогом товаров с пагинацией, поиском и фильтрацией
- Корзиной на основе Django sessions
- Оформлением заказов с email-уведомлениями
- Личным кабинетом (регистрация, вход, история заказов, редактирование профиля)
- Отзывами на товары (только после подтверждённой покупки)
- REST API с JWT-авторизацией и Swagger-документацией
- Админ-панелью с аналитикой продаж

**Стек:** Django 5, DRF, PostgreSQL, Docker, JWT (SimpleJWT), drf-spectacular

---

## Установка и запуск через Docker

### Требования

- Docker и Docker Compose

### Первый запуск

```bash
# Клонировать репозиторий
git clone <repo-url>
cd Django_myshop_M3

# Собрать и запустить контейнеры
docker compose up --build
```

Дождитесь сообщения от `db`: `database system is ready to accept connections`.

### Миграции и начальные данные

```bash
# Подключиться к контейнеру web
docker compose exec web bash

# Внутри контейнера:
python manage.py migrate

# Загрузить тестовые данные (категории и товары)
python manage.py loaddata products/fixtures/categories.json
python manage.py loaddata products/fixtures/products.json

# Создать superuser для админ-панели
python manage.py createsuperuser

exit
```

### Доступные адреса

| URL | Описание |
|-----|----------|
| `http://127.0.0.1:8000/` | Каталог товаров |
| `http://127.0.0.1:8000/admin/` | Админ-панель |
| `http://127.0.0.1:8000/api/v1/docs/` | Swagger API документация |
| `http://127.0.0.1:8000/account/` | Личный кабинет |

---

## JWT и примеры API

### Получение токенов

```bash
# Регистрация
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "email": "user1@example.com", "password": "StrongPass123"}'

# Вход (получить access + refresh токены)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "StrongPass123"}'
```

Ответ:
```json
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

### Обновление access токена

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```

### Примеры запросов

```bash
# Список товаров (без авторизации)
curl http://127.0.0.1:8000/api/v1/products/

# Поиск и фильтрация
curl "http://127.0.0.1:8000/api/v1/products/?search=hops&price=5.99"

# Список своих заказов (JWT required)
curl http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer <your_access_token>"

# Создание заказа (JWT required, корзина должна быть не пустой)
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe", "phone": "+380991234567", "city": "Kyiv", "address": "Khreshchatyk 1"}'

# Отменить заказ
curl -X PATCH http://127.0.0.1:8000/api/v1/orders/1/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'

# Отзывы на товар (GET — без авторизации, POST — JWT required)
curl http://127.0.0.1:8000/api/v1/products/1/reviews/
```

> Полная интерактивная документация: `http://127.0.0.1:8000/api/v1/docs/`

---

## Запуск тестов и линтеров

```bash
# Поднять сервисы (если не запущены)
docker compose up -d

# Запустить все проверки сразу
docker compose exec web bash -lc "bash scripts/run_checks.sh"
```

Или по отдельности:

```bash
# pytest
docker compose exec web python -m pytest -q

# mypy (проверка типов)
docker compose exec web python -m mypy .

# ruff (линтер)
docker compose exec web python -m ruff check .
```

Пример успешного результата:

```
27 passed in 5.10s
mypy: no errors
```

---

## Структура проекта

```
Django_myshop_M3/
├── api/                  # DRF: ViewSets, serializers, JWT endpoints
├── core/                 # settings, urls, wsgi/asgi
├── orders/               # модели Order/OrderItem, корзина (sessions), checkout
├── products/             # модели Product/Category, каталог, страница товара
├── reviews/              # модель Review, логика отзывов
├── users/                # регистрация, профиль, личный кабинет
├── templates/            # Django HTML-шаблоны
├── static/               # CSS, JS, изображения
├── tests/                # pytest тесты (models, views, api, cart)
│   ├── test_models.py
│   ├── test_api.py
│   ├── test_api_rest.py
│   ├── test_cart.py
│   ├── test_views.py
│   └── test_registration.py
├── scripts/              # вспомогательные скрипты (run_checks.sh)
├── compose.yaml          # Docker Compose конфигурация
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── ruff.toml
└── setup.cfg             # mypy / flake8 конфигурация
```
