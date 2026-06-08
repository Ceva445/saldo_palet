# Pallet Logistics System

Облік деревʼяних палет на логістичному складі (FastAPI + SQLAlchemy + Alembic, ванільний JS-фронтенд).
Один екран-CRM: Przyjęcia (IN), Wydania (OUT), Korekta stanu, Masterdata (Obszar / Dostawca / Jednostka)
та таблиця стану. Доступ до кожного компонента визначається роллю — і на API, і в UI.

## Ролі та дозволи

| Роль     | masterdata | receipts | releases | corrections | reports |
|----------|:----------:|:--------:|:--------:|:-----------:|:-------:|
| admin    | ✅         | ✅       | ✅       | ✅          | ✅      |
| operator | —          | ✅       | ✅       | ✅          | ✅      |
| viewer   | —          | —        | —        | —           | ✅      |

Дозволи задаються в `app/services/permission_service.py`. На API їх застосовують
`require_permission(...)` (masterdata) і перевірка за типом транзакції в `app/routers/transaction.py`.
UI отримує список дозволів через `GET /auth/me` і блокує (робить видимими, але неактивними)
секції, до яких немає прав.

## Запуск

```bash
# 1. Налаштувати .env (DATABASE_URL, SECRET_KEY)
# 2. Міграції + сід (ролі + адмін) + сервер:
./start.sh
```

Початковий користувач: `admin` / `admin123` (змінюється через env `ADMIN_USERNAME`, `ADMIN_PASSWORD`).
Фронтенд: http://localhost:8000/ , API-документація: http://localhost:8000/docs

## Тести

```bash
pytest
```
