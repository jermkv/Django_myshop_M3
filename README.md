Первый запуск
docker compose up --build

Следите за логами: db должен показать "database system is ready to accept connections".

Подключитесь к контейнеру web:
docker compose exec web bash

Это откроет терминал внутри контейнера web (где Django установлен).

Примените миграции (внутри контейнера)
python manage.py migrate
Это создаст все таблицы в БД. Должно пройти без ошибок, если db готов.

При необходимости работы с тестовыми данными, загрузите фикстуры (внутри контейнера):
python manage.py loaddata products/fixtures/categories.json
python manage.py loaddata products/fixtures/products.json
Это добавит тестовые данные (категории и продукты).

Выйдите из контейнера
exit (чтобы выйти из bash в контейнере).

Для входа на админ-панель необходимо создаь учетную запись superuser:
python manage.py createsuperuser

Если аккаунт уже создан, перейдите по адресу http://127.0.0.1:8000/admin/ и введите логин и пароль вашего superuser.

Тесты и статические проверки
----------------------------

В проекте настроены unit/integ тесты (`pytest`) и статическая проверка типов (`mypy`).
Рекомендуемый способ выполнить все проверки внутри контейнера `web`:

```bash
# поднимите сервисы (если не запущены)
docker compose up -d

# запустить проверки (pytest + mypy, опционально flake8)
docker compose exec web bash -lc "bash scripts/run_checks.sh"
```

Отдельные команды внутри контейнера:

```bash
docker compose exec web python -m pytest -q
docker compose exec web python -m mypy .
# flake8 (если установлен в окружении)
docker compose exec web flake8 .
```

Пример успешного результата (прошлый прогон):

```
23 passed in 4.30s
mypy: no errors
```

Если вы предпочитаете запускать тесты локально (не в контейнере), установите зависимости и выполните `python -m pytest` и `python -m mypy .` в вашем виртуальном окружении.

