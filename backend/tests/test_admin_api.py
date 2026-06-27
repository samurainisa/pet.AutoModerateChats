from datetime import datetime, timedelta

from app.extensions import db
from app.models import Message, ModerationAction, Setting, User, Violation


def test_admin_stats_and_settings_and_user_patch(app, client, login_user, create_user):
    with app.app_context():
        admin = login_user("admin_stats", role="admin")
        user_a = create_user("admin_user_a")
        user_b = create_user("admin_user_b")
        user_a_id = user_a.id
        now = datetime.utcnow()

        db.session.add_all(
            [
                Message(
                    room="public",
                    user_id=user_a.id,
                    text_original="ok msg",
                    text_normalized="ok msg",
                    status="ok",
                    created_at=now - timedelta(minutes=1),
                ),
                Message(
                    room="public",
                    user_id=user_a.id,
                    text_original="hidden msg",
                    text_normalized="hidden msg",
                    status="hidden",
                    created_at=now - timedelta(minutes=1),
                ),
                Message(
                    room="public",
                    user_id=user_b.id,
                    text_original="blocked msg",
                    text_normalized="blocked msg",
                    status="blocked",
                    created_at=now - timedelta(minutes=1),
                ),
                Message(
                    room="public",
                    user_id=user_b.id,
                    text_original="approved msg",
                    text_normalized="approved msg",
                    status="approved_manual",
                    created_at=now - timedelta(minutes=1),
                ),
            ]
        )
        db.session.flush()
        msg_ids = [row.id for row in Message.query.all()]
        db.session.add_all(
            [
                Violation(user_id=user_a_id, message_id=msg_ids[1], violation_type="toxicity", score=0.6),
                Violation(user_id=user_b.id, message_id=msg_ids[2], violation_type="flood", score=0.9),
                Violation(user_id=user_b.id, message_id=msg_ids[2], violation_type="toxicity", score=0.8),
            ]
        )
        db.session.commit()
        assert admin.id > 0

    stats_response = client.get("/api/admin/stats")
    assert stats_response.status_code == 200
    stats = stats_response.get_json()
    assert stats["messages_total"] == 4
    assert stats["messages_ok"] == 2
    assert stats["messages_hidden"] == 1
    assert stats["messages_blocked"] == 1
    assert len(stats["top_violators"]) >= 1

    settings_response = client.patch(
        "/api/admin/settings",
        json={
            "low_threshold": 0.33,
            "high_threshold": 0.8,
            "flood_count": 7,
            "flood_window": 45,
            "duplicate_window": 20,
            "temp_block_hours": 12,
        },
    )
    assert settings_response.status_code == 200
    updated = settings_response.get_json()["updated"]
    assert updated["flood_count"] == 7

    with app.app_context():
        setting = db.session.get(Setting, "flood_count")
        assert setting.value == "7"

    user_patch = client.patch(
        f"/api/admin/users/{user_a_id}",
        json={
            "role": "moderator",
            "is_blocked": True,
            "blocked_until": "2026-04-01T12:00:00Z",
            "warnings": 2,
            "rating_score": 0.95,
            "shadow_ban": True,
        },
    )
    assert user_patch.status_code == 200
    patched_user = user_patch.get_json()["user"]
    assert patched_user["role"] == "moderator"
    assert patched_user["is_blocked"] is True
    assert patched_user["warnings"] == 2
    assert patched_user["rating_score"] == 0.95
    assert patched_user["shadow_ban"] is True


def test_admin_access_and_validation_errors(app, client, create_user, login_user):
    with app.app_context():
        target = create_user("admin_target")
        target_id = target.id
        login_user("regular_user_forbidden", role="user")

    forbidden_stats = client.get("/api/admin/stats")
    assert forbidden_stats.status_code == 403

    client.post("/api/auth/logout")
    login_user("real_admin", role="admin")

    no_changes = client.patch("/api/admin/settings", json={})
    assert no_changes.status_code == 200
    assert no_changes.get_json()["updated"] == {}

    bad_setting = client.patch("/api/admin/settings", json={"flood_count": "x"})
    assert bad_setting.status_code == 400
    assert bad_setting.get_json()["error"] == "invalid_value:flood_count"

    invalid_role = client.patch(f"/api/admin/users/{target_id}", json={"role": "root"})
    assert invalid_role.status_code == 400
    assert invalid_role.get_json()["error"] == "invalid_role"

    invalid_until = client.patch(f"/api/admin/users/{target_id}", json={"blocked_until": "bad-date"})
    assert invalid_until.status_code == 400
    assert invalid_until.get_json()["error"] == "invalid_blocked_until"

    invalid_warnings = client.patch(f"/api/admin/users/{target_id}", json={"warnings": "bad"})
    assert invalid_warnings.status_code == 400
    assert invalid_warnings.get_json()["error"] == "invalid_warnings"

    invalid_rating = client.patch(f"/api/admin/users/{target_id}", json={"rating_score": "bad"})
    assert invalid_rating.status_code == 400
    assert invalid_rating.get_json()["error"] == "invalid_rating_score"

    not_found = client.patch("/api/admin/users/99999", json={"role": "user"})
    assert not_found.status_code == 404


def test_admin_threshold_change_affects_next_pipeline_decision(app, client, login_user):
    class MidHighClassifier:
        def score(self, _text: str):
            return {"aggregate": 0.65, "labels": {"insult": 0.65}, "fallback": False}

    with app.app_context():
        admin = login_user("admin_threshold", role="admin")
        assert admin.role == "admin"

    patch = client.patch("/api/admin/settings", json={"high_threshold": 0.6})
    assert patch.status_code == 200
    assert patch.get_json()["updated"]["high_threshold"] == 0.6

    with app.app_context():
        user = User(username="threshold_user", password_hash="x", role="user")
        db.session.add(user)
        db.session.commit()
        pipeline = app.extensions["moderation_pipeline"]
        pipeline.classifier = MidHighClassifier()

        result = pipeline.process_message(user=user, room="public", text="threshold test")
        assert result["status"] == "blocked"


def test_admin_users_list_and_profile(app, client, login_user, create_user):
    with app.app_context():
        login_user("admin_profile_access", role="admin")
        target_user = create_user(
            "profile_target",
            email="profile_target@example.com",
            warnings=1,
            rating_score=0.44,
            shadow_ban=True,
        )
        moderator = create_user("profile_moderator", role="moderator")
        now = datetime.utcnow()

        message = Message(
            room="public",
            user_id=target_user.id,
            text_original="profile message",
            text_normalized="profile message",
            status="hidden",
            toxicity_score=0.51,
            decision_reason="rule_warn:link",
            created_at=now - timedelta(minutes=2),
        )
        db.session.add(message)
        db.session.flush()

        db.session.add(
            Violation(
                user_id=target_user.id,
                message_id=message.id,
                violation_type="toxicity",
                score=0.51,
                created_at=now - timedelta(minutes=1),
            )
        )
        db.session.add(
            ModerationAction(
                message_id=message.id,
                moderator_id=moderator.id,
                action="approve",
                comment="ok",
                created_at=now,
            )
        )
        db.session.commit()

        target_user_id = target_user.id

    users_response = client.get("/api/admin/users")
    assert users_response.status_code == 200
    users_payload = users_response.get_json()
    assert "items" in users_payload
    user_row = next((item for item in users_payload["items"] if item["id"] == target_user_id), None)
    assert user_row is not None
    assert user_row["messages_total"] >= 1
    assert user_row["violations_total"] >= 1

    profile_response = client.get(f"/api/admin/users/{target_user_id}")
    assert profile_response.status_code == 200
    profile_payload = profile_response.get_json()
    assert profile_payload["user"]["id"] == target_user_id
    assert profile_payload["summary"]["messages_total"] >= 1
    assert profile_payload["summary"]["violations_total"] >= 1
    assert len(profile_payload["messages"]) >= 1
    assert len(profile_payload["violations"]) >= 1
    assert len(profile_payload["moderation_actions"]) >= 1
