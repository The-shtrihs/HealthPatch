# Практична робота №6 — Естимація проєкту Health Patch

**Команда:** Marchenko D. · Kramarenko M. · Loban M. · Bondarchuk O. (PM)
**Проєкт:** Health Patch — gamified fitness platform (FastAPI / PostgreSQL)
**Метод естимації:** Planning Poker з одиницями Фібоначчі
**Одиниця:** 🐷 (свиня) — замість цифр кількість свиней за шкалою Фібоначчі

---

## Шкала оцінювання

| Свині | Складність | Орієнтовно |
|---|---|---|
| 🐷 | Тривіальна | ~1 год |
| 🐷🐷 | Проста | ~2 год |
| 🐷🐷🐷 | Нижче середнього | ~3 год |
| 🐷🐷🐷🐷🐷 | Середня | ~5 год |
| 🐷🐷🐷🐷🐷🐷🐷🐷 | Складна | ~8 год |
| 🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷 | Дуже складна | ~13 год |
| 🐷×21 | Занадто велика — треба ділити | — |

> **Правило:** оцінку 🐷×21 і більше — не беремо в спринт, обов'язково декомпозуємо далі.
> **1 🐷 ≈ 1 година роботи** — коефіцієнт обраний командою на Planning Poker.

---

## Техніка оцінювання

Використовується **комбінація WBS + Experience-based + Planning Poker**:

1. PM розбив проєкт на задачі по доменах (WBS)
2. Кожен власник домену оцінив свої задачі самостійно (Experience-based)
3. Команда звірила оцінки на Planning Poker — де розкид > 2 позицій по шкалі, проводились дебати
4. Фінальна оцінка — після переголосування з урахуванням аргументів

---

## Domain 1 — Identity & Auth
**Власник: Daniil Marchenko**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 1.1 | Модель USER + USER_PROFILE + REFRESH_TOKEN, міграція | 🐷🐷🐷 | 3 | Три таблиці, зв'язки, enum-поля — стандартно |
| 1.2 | Реєстрація: валідація, Argon2, верифікаційний email | 🐷🐷🐷🐷🐷 | 5 | Argon2 + фонова задача email + rate limit |
| 1.3 | Логін: перевірка хешу, генерація JWT access + refresh | 🐷🐷🐷🐷🐷 | 5 | Дві гілки: з 2FA і без, device_info |
| 1.4 | OAuth: Google / GitHub / Facebook + Redis state | 🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷🐷 | 13 | Три провайдери, callback, state в Redis, TTL |
| 1.5 | Email верифікація + повторне надсилання | 🐷🐷🐷 | 3 | Token validation, is_verified, rate limit |
| 1.6 | Forgot password + reset password | 🐷🐷🐷🐷🐷 | 5 | Два ендпоінти, токен, Argon2, rate limit |
| 1.7 | Change password (авторизований) | 🐷🐷 | 2 | Перевірка поточного + хешування нового |
| 1.8 | Refresh token endpoint + logout + logout-all | 🐷🐷🐷🐷🐷 | 5 | Revoke логіка, DB lookup, bulk revoke |
| 1.9 | 2FA: enable → QR → confirm → disable → verify on login | 🐷🐷🐷🐷🐷🐷🐷🐷 | 8 | pyotp, 5 ендпоінтів, temp_token, rate limit |
| 1.10 | GET /auth/me + PATCH /profile/me + PUT fitness + DELETE | 🐷🐷🐷🐷🐷 | 5 | Чотири ендпоінти, BMI на льоту, soft delete |
| 1.11 | get_current_user dependency (middleware для всього API) | 🐷🐷🐷 | 3 | Dependency injection, JWT decode, 401 |
| **Разом** | | | **57 год** | |

---

## Domain 2 — Activity & Workouts
**Власник: Maksym Kramarenko**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 2.1 | Моделі (всі 10 таблиць Activity) + міграції | 🐷🐷🐷🐷🐷🐷🐷🐷 | 8 | Найбільший домен: 10 таблиць, junction table, CASCADE |
| 2.2 | Muscle Groups CRUD (create + list) | 🐷🐷 | 2 | Дві прості операції, унікальність |
| 2.3 | Exercises: create + search з пагінацією + detail | 🐷🐷🐷🐷🐷 | 5 | Junction table secondary, пагінація, фільтр |
| 2.4 | Workout Plans CRUD (create / update / delete / list) | 🐷🐷🐷🐷🐷🐷🐷🐷 | 8 | Nested структура при create, авторство, cascade delete |
| 2.5 | Public feed планів з пагінацією | 🐷🐷 | 2 | Простий SELECT з фільтром is_public |
| 2.6 | Plan Trainings: add + delete (з перевіркою авторства) | 🐷🐷🐷 | 3 | Авторство, weekday enum, order_num |
| 2.7 | Plan Training Exercises: add + delete | 🐷🐷🐷 | 3 | target_weight_pct, order, перевірка FK |
| 2.8 | Workout Sessions: start + end + list + detail | 🐷🐷🐷🐷🐷 | 5 | started_at / ended_at, duration_minutes, належність |
| 2.9 | Exercise Session: add exercise до сесії | 🐷🐷 | 2 | Перевірка що сесія не ended, order_num |
| 2.10 | Workout Sets: log set (set_number, reps, weight) | 🐷🐷 | 2 | Валідація > 0, належність через сесію |
| 2.11 | Personal Records: list + upsert + delete | 🐷🐷🐷 | 3 | Upsert (unique constraint), recorded_at |
| **Разом** | | | **43 год** | |

---

## Domain 3 — Nutrition & Diet
**Власник: Mykhailo Loban**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 3.1 | Моделі FOOD + FOOD_PORTION + DAILY_DIARY + MEAL_ENTRY + міграції | 🐷🐷🐷🐷🐷 | 5 | 4 таблиці, unique constraint (user, date), enum meal_type |
| 3.2 | Food search + detail (тільки is_verified=true, пагінація) | 🐷🐷🐷 | 3 | Search by name, фільтр verified |
| 3.3 | Food Portions list по food_id | 🐷🐷 | 2 | Простий SELECT з FK |
| 3.4 | Daily macro norm calculation (за профілем юзера) | 🐷🐷🐷🐷🐷 | 5 | Формула (вік, вага, ріст, стать, ціль), перевірка повноти профілю |
| 3.5 | Day overview: норма vs спожите vs залишок | 🐷🐷🐷🐷🐷 | 5 | JOIN diary + meal_entry + food, агрегація макросів |
| 3.6 | Add meal entry (find-or-create diary, розрахунок remaining) | 🐷🐷🐷🐷🐷 | 5 | Upsert diary, обчислення макросів за weight_grams |
| 3.7 | Delete meal entry + перерахунок remaining | 🐷🐷🐷 | 3 | Перевірка належності, recalculate |
| 3.8 | Update daily diary (water_ml + notes) | 🐷🐷 | 2 | Find-or-create, два поля |
| 3.9 | Admin: верифікація food (is_verified flag) | 🐷🐷 | 2 | Один PATCH, перевірка role=admin |
| 3.10 | Food data script (завантаження бази продуктів) | 🐷🐷🐷🐷🐷 | 5 | CSV/JSON parsing, bulk insert, fdc_id |
| **Разом** | | | **37 год** | |

---

## Domain 4 — Social
**Власник: Maksym Kramarenko** *(разом з Activity)*

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 4.1 | Like / unlike план (toggle логіка) | 🐷🐷 | 2 | Compound PK, idempotent |
| 4.2 | Comments: add + delete (тільки автор) | 🐷🐷🐷 | 3 | Авторство на delete, text validation |
| 4.3 | Bookmarks: add + remove | 🐷🐷 | 2 | Compound PK, аналогічно до like |
| **Разом** | | | **7 год** | |

---

## Domain 5 — Gamification (RPG)
**Власник: TBD (розподілено між командою)**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 5.1 | Моделі CHARACTER + CHARACTER_STAT + ACHIEVEMENT + USER_ACHIEVEMENT + міграції | 🐷🐷🐷 | 3 | 4 таблиці, але прості структури |
| 5.2 | Character creation (on first access, class selection) | 🐷🐷🐷 | 3 | One-to-one з user, початкові стати |
| 5.3 | XP awarding після завершення сесії (інтеграція з Activity) | 🐷🐷🐷🐷🐷 | 5 | Формула XP, atomic update, cross-domain |
| 5.4 | Level up logic + stats increment | 🐷🐷🐷 | 3 | Threshold check, stat formula |
| 5.5 | Achievements: перевірка після XP update | 🐷🐷🐷🐷🐷 | 5 | Bulk check всіх ACHIEVEMENT, no duplicates |
| **Разом** | | | **19 год** | |

---

## Domain 6 — AI Coach
**Власник: TBD**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 6.1 | Модель AI_WORKOUT_PLAN + міграція | 🐷 | 1 | Одна проста таблиця |
| 6.2 | Plan generation: збір профілю + history + запит до AI API | 🐷🐷🐷🐷🐷🐷🐷🐷 | 8 | External API call, async, raw_ai_response JSON |
| 6.3 | Accept / reject plan (is_accepted + create WORKOUT_PLAN) | 🐷🐷🐷🐷🐷 | 5 | Дві гілки, cross-domain create |
| 6.4 | Graceful degradation якщо AI недоступний | 🐷🐷 | 2 | Try/except, user-friendly error |
| **Разом** | | | **16 год** | |

---

## Інфраструктура та Cross-cutting
**Власник: уся команда / PM**

| # | Задача | Свині | Год | Обґрунтування |
|---|--------|-------|-----|---------------|
| 7.1 | Docker Compose (db + redis + api) + health checks | 🐷🐷🐷 | 3 | Три сервіси, depends_on, volumes |
| 7.2 | Alembic base setup + env.py | 🐷🐷 | 2 | Конфігурація, env.py |
| 7.3 | GitHub Actions CI (Ruff lint on PR) | 🐷🐷 | 2 | YAML пайплайн |
| 7.4 | Rate limiting middleware (Redis sliding window) | 🐷🐷🐷🐷🐷 | 5 | Configurable per endpoint, Redis |
| 7.5 | Pydantic-settings конфіг + .env.example | 🐷🐷 | 2 | Стандартно |
| 7.6 | Error handling (custom exceptions hierarchy) | 🐷🐷🐷 | 3 | error_code, message, timestamp, path |
| 7.7 | Email templates (Jinja2) для верифікації та reset | 🐷🐷🐷 | 3 | Два шаблони |
| **Разом** | | | **20 год** | |

---

## Зведена таблиця по доменах

| Домен | Власник | Задач | Годин |
|---|---|---|---|
| Identity & Auth | Marchenko D. | 11 | 57 |
| Activity & Workouts | Kramarenko M. | 11 | 43 |
| Nutrition & Diet | Loban M. | 10 | 37 |
| Social | Kramarenko M. | 3 | 7 |
| Gamification | TBD | 5 | 19 |
| AI Coach | TBD | 4 | 16 |
| Інфраструктура | Команда | 7 | 20 |
| **Разом** | | **51** | **199 год** |

---

## Розподіл годин по розробниках

| Розробник | Домени | Годин |
|---|---|---|
| Marchenko D. | Identity & Auth + частина інфра | ~64 год |
| Kramarenko M. | Activity + Social + частина інфра | ~57 год |
| Loban M. | Nutrition + частина інфра | ~44 год |
| TBD / спільно | Gamification + AI + інфра | ~34 год |

> **Примітка:** Gamification та AI Coach наразі не мають призначеного власника (TBD в `techreq.md`). Годинник розподіляться між командою на наступному Sprint Planning.

---

## Ризики та поправочні коефіцієнти

Застосовано **Three-Point Estimation** для ризикових задач:

| Ризик | Задачі | Коефіцієнт |
|---|---|---|
| OAuth (три провайдери, складна логіка) | 1.4 | ×1.5 → вже закладено в 13 год |
| AI API (зовнішня залежність, нестабільність) | 6.2 | ×1.5 → вже закладено в 8 год |
| Gamification XP (cross-domain, atomic) | 5.3 | ×1.5 → вже закладено в 5 год |
| Академічне навантаження команди (сесія) | всі | загальний буфер +15% |

**З урахуванням буфера:**
`199 год × 1.15 ≈ **229 годин** загальна оцінка проєкту`

---

## Бюджет (опційно)

Якщо оцінювати як Junior/Middle команду на аутсорсі:

| Рівень | Ставка | Годин | Сума |
|---|---|---|---|
| Junior Developer × 3 | $15/год | 199 | ~$2 985 |
| PM × 1 (20% часу) | $20/год | 40 | ~$800 |
| **Разом** | | **239 год** | **~$3 785** |

> Реальний проєкт виконується командою студентів в навчальних цілях — бюджет наведено для ілюстрації техніки естимації.

---

## Висновок

Проєкт оцінено методом **WBS + Experience-based + Planning Poker** зі шкалою 🐷 (свиней Фібоначчі). Загальний обсяг — **~199 годин чистої розробки** (229 з буфером на ризики).

Найважчий домен — **Identity & Auth** (57 год): OAuth, 2FA, refresh token management.
Найбільший домен за кількістю таблиць — **Activity & Workouts** (10 таблиць, 43 год).
Найменш визначений — **Gamification + AI** (TBD власник, ~35 год сумарно).
