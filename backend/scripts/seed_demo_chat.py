from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Message, ModerationAction, Setting, User, Violation


DEMO_PREFIX = "[DEMO-CHAT]"


@dataclass(frozen=True)
class DemoUserSpec:
    username: str
    password: str
    role: str = "user"


DEMO_USERS: list[DemoUserSpec] = [
    DemoUserSpec(username="demo_user_1", password="demo12345"),
    DemoUserSpec(username="demo_user_2", password="demo12345"),
    DemoUserSpec(username="demo_user_3", password="demo12345"),
    DemoUserSpec(username="demo_user_4", password="demo12345"),
    DemoUserSpec(username="demo_user_5", password="demo12345"),
]


SAFE_TEMPLATES = [
    "Всем привет! Как проходит день?",
    "Я сегодня настраивал окружение для проекта.",
    "Кто уже проверял новую версию интерфейса?",
    "Давайте вечером обсудим план задач на неделю.",
    "Спасибо за помощь с тестами, стало понятнее.",
    "Предлагаю вынести логику модерации в отдельный сервис.",
    "Мне нравится идея с очередью скрытых сообщений.",
    "Я добавил пару фиксов в форму входа.",
    "Можно потом сверить результаты по нагрузке?",
    "Проверьте, пожалуйста, мои изменения в ветке.",
    "Сделал небольшую оптимизацию в обработке сообщений.",
    "Хочу уточнить пороги для токсичности и скрытия.",
    "Давайте соберем короткий отчет по прогону тестов.",
    "Я сейчас обновляю документацию для запуска.",
    "Если нужно, могу помочь с панелью администратора.",
]

SHADOW_TEMPLATES = [
    "Напишу еще одно сообщение для проверки модерации.",
    "Проверяю, как отрабатывает скрытие сообщений.",
    "Сообщение без нарушений, но должно быть скрыто.",
    "Тестируем очередь модератора на реальных данных.",
    "Это сообщение также пойдет в скрытые.",
    "Проверка механизма hidden для одного пользователя.",
    "Сообщение в рамках demo-набора для тестирования.",
    "Смотрим, как пополняется очередь скрытых.",
]


def _ensure_user(spec: DemoUserSpec) -> User:
    user = User.query.filter_by(username=spec.username).first()
    password_hash = generate_password_hash(spec.password)
    if user is None:
        user = User(
            username=spec.username,
            password_hash=password_hash,
            role=spec.role,
            rating_score=0.0,
            warnings=0,
            is_blocked=False,
            blocked_until=None,
            shadow_ban=False,
        )
        db.session.add(user)
    else:
        user.password_hash = password_hash
        user.role = spec.role
        user.rating_score = 0.0
        user.warnings = 0
        user.is_blocked = False
        user.blocked_until = None
        user.shadow_ban = False
    return user


def _clear_previous_demo_messages(user_ids: list[int]) -> None:
    if not user_ids:
        return

    message_ids: list[int] = [
        row.id
        for row in db.session.query(Message.id)
        .filter(Message.user_id.in_(user_ids))
        .all()
    ]
    if not message_ids:
        return

    db.session.query(Violation).filter(Violation.message_id.in_(message_ids)).delete(synchronize_session=False)
    db.session.query(ModerationAction).filter(ModerationAction.message_id.in_(message_ids)).delete(synchronize_session=False)
    db.session.query(Message).filter(Message.id.in_(message_ids)).delete(synchronize_session=False)
    db.session.commit()


def _set_setting(key: str, value: str) -> str:
    row = db.session.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        db.session.add(row)
        db.session.commit()
        return value

    old = row.value
    row.value = value
    db.session.commit()
    return old


def _safe_message(i: int, username: str) -> str:
    template = SAFE_TEMPLATES[i % len(SAFE_TEMPLATES)]
    return f"{DEMO_PREFIX} [SAFE {i:03d}] {username}: {template}"


def _shadow_message(i: int, username: str) -> str:
    template = SHADOW_TEMPLATES[i % len(SHADOW_TEMPLATES)]
    return f"{DEMO_PREFIX} [SHADOW {i:03d}] {username}: {template}"


def _duplicate_pairs_for_users(users: Iterable[User]) -> list[tuple[User, str]]:
    items: list[tuple[User, str]] = []
    for idx, user in enumerate(users, start=1):
        for pair in range(1, 3):
            text = f"{DEMO_PREFIX} [DUP-{idx}-{pair}] повторяющийся текст для проверки duplicate"
            # first should be ok, second should be blocked (duplicate)
            items.append((user, text))
            items.append((user, text))
    return items


def main() -> None:
    app = create_app()
    generated = 0
    old_flood_count = None

    with app.app_context():
        users = [_ensure_user(spec) for spec in DEMO_USERS]
        db.session.commit()
        _clear_previous_demo_messages([user.id for user in users])

        # Disable flood side-effect for bulk demo generation.
        old_flood_count = _set_setting("flood_count", "1000")

        pipeline = app.extensions["moderation_pipeline"]

        # 140 safe messages, distributed among 5 users.
        for i in range(140):
            user = users[i % len(users)]
            text = _safe_message(i, user.username)
            result = pipeline.process_message(user=user, room="public", text=text)
            if result.get("message") is not None:
                generated += 1

        # Enable shadow-ban for user #5 and send 40 messages -> hidden.
        shadow_user = users[4]
        shadow_user.shadow_ban = True
        db.session.add(shadow_user)
        db.session.commit()

        for i in range(140, 180):
            text = _shadow_message(i, shadow_user.username)
            result = pipeline.process_message(user=shadow_user, room="public", text=text)
            if result.get("message") is not None:
                generated += 1

        # 20 messages via duplicate pairs: 10 ok + 10 blocked (duplicate).
        for user, text in _duplicate_pairs_for_users(users):
            result = pipeline.process_message(user=user, room="public", text=text)
            if result.get("message") is not None:
                generated += 1

        # Restore original flood_count.
        if old_flood_count is not None:
            _set_setting("flood_count", old_flood_count)

        rows = (
            Message.query.filter(Message.text_original.like(f"{DEMO_PREFIX}%"))
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )

        status_counter = Counter(row.status for row in rows)
        user_counter = Counter(row.author.username if row.author else str(row.user_id) for row in rows)

        print("=== DEMO CHAT SEED COMPLETE ===")
        print(f"timestamp: {datetime.utcnow().isoformat()}Z")
        print(f"messages_saved: {len(rows)} (generated_attempts: {generated})")
        print(f"expected: 200")
        print("status_counts:")
        for key in sorted(status_counter.keys()):
            print(f"  {key}: {status_counter[key]}")
        print("user_counts:")
        for key in sorted(user_counter.keys()):
            print(f"  {key}: {user_counter[key]}")
        print("users_credentials:")
        for spec in DEMO_USERS:
            print(f"  {spec.username} / {spec.password}")


if __name__ == "__main__":
    main()
