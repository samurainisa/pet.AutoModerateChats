from app.extensions import db, socketio
from app.models import Message, User


def test_socket_connect_requires_auth(app):
    socket_client = socketio.test_client(app, namespace="/chat")
    assert not socket_client.is_connected("/chat")


def test_socket_join_leave_and_send_ok_message(app, client, login_user):
    login_user("socket_user")
    socket_client = socketio.test_client(app, flask_test_client=client, namespace="/chat")
    assert socket_client.is_connected("/chat")

    connected_events = socket_client.get_received("/chat")
    assert any(event["name"] == "connected" for event in connected_events)

    socket_client.emit("join_room", {"room": "private"}, namespace="/chat")
    denied_join = socket_client.get_received("/chat")
    assert any(event["name"] == "error" for event in denied_join)

    socket_client.emit("join_room", {"room": "public"}, namespace="/chat")
    joined_events = socket_client.get_received("/chat")
    assert any(event["name"] == "joined_room" for event in joined_events)

    socket_client.emit("send_message", {"room": "public", "text": "socket hello"}, namespace="/chat")
    message_events = socket_client.get_received("/chat")
    assert any(event["name"] == "new_message" for event in message_events)

    socket_client.emit("leave_room", {"room": "public"}, namespace="/chat")
    left_events = socket_client.get_received("/chat")
    assert any(event["name"] == "left_room" for event in left_events)

    with app.app_context():
        assert Message.query.count() == 1

    socket_client.disconnect(namespace="/chat")


def test_socket_send_message_validation_and_room_errors(app, client, login_user):
    login_user("socket_validation")
    socket_client = socketio.test_client(app, flask_test_client=client, namespace="/chat")
    socket_client.get_received("/chat")

    socket_client.emit("send_message", {"room": "private", "text": "hello"}, namespace="/chat")
    room_error = socket_client.get_received("/chat")
    assert any(event["name"] == "message_blocked" and event["args"][0]["reason"] == "room_not_allowed" for event in room_error)

    socket_client.emit("send_message", {"room": "public", "text": "    "}, namespace="/chat")
    validation_error = socket_client.get_received("/chat")
    assert any(event["name"] == "message_blocked" and event["args"][0]["reason"] == "text_required" for event in validation_error)


def test_socket_send_message_unauthorized_after_logout(app, client, login_user):
    login_user("socket_logout")
    socket_client = socketio.test_client(app, flask_test_client=client, namespace="/chat")
    socket_client.get_received("/chat")

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    socket_client.emit("send_message", {"room": "public", "text": "hello after logout"}, namespace="/chat")
    blocked = socket_client.get_received("/chat")
    assert any(event["name"] == "message_blocked" and event["args"][0]["reason"] == "unauthorized" for event in blocked)


def test_socket_send_message_user_not_found(app, client, create_user, monkeypatch):
    with app.app_context():
        user = create_user("socket_deleted")
        user_id = user.id

    login = client.post("/api/auth/login", json={"username": "socket_deleted", "password": "password"})
    assert login.status_code == 200

    socket_client = socketio.test_client(app, flask_test_client=client, namespace="/chat")
    socket_client.get_received("/chat")

    with app.app_context():
        assert db.session.get(User, user_id) is not None

    monkeypatch.setattr("app.sockets.chat.get_current_user", lambda: None)

    socket_client.emit("send_message", {"room": "public", "text": "hello missing user"}, namespace="/chat")
    blocked = socket_client.get_received("/chat")
    assert any(event["name"] == "message_blocked" and event["args"][0]["reason"] == "user_not_found" for event in blocked)


def test_socket_hidden_flow_to_moderator_room(app, create_user):
    moderator_client = app.test_client()
    shadow_client = app.test_client()

    with app.app_context():
        create_user("socket_mod", role="moderator")
        create_user("socket_shadow", shadow_ban=True)

    mod_login = moderator_client.post("/api/auth/login", json={"username": "socket_mod", "password": "password"})
    assert mod_login.status_code == 200
    shadow_login = shadow_client.post("/api/auth/login", json={"username": "socket_shadow", "password": "password"})
    assert shadow_login.status_code == 200

    mod_socket = socketio.test_client(app, flask_test_client=moderator_client, namespace="/chat")
    shadow_socket = socketio.test_client(app, flask_test_client=shadow_client, namespace="/chat")
    assert mod_socket.is_connected("/chat")
    assert shadow_socket.is_connected("/chat")
    mod_socket.get_received("/chat")
    shadow_socket.get_received("/chat")

    shadow_socket.emit("send_message", {"room": "public", "text": "hidden message"}, namespace="/chat")

    moderator_events = mod_socket.get_received("/chat")
    assert any(event["name"] == "message_hidden" for event in moderator_events)

    sender_events = shadow_socket.get_received("/chat")
    assert any(event["name"] == "message_updated" and event["args"][0]["status"] == "hidden" for event in sender_events)
