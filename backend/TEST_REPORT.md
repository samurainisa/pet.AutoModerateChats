# Test Report: AutoModerateChatPrototype (Backend)

## 1) Summary

- Date: 2026-04-01
- Test command: `python -m pytest -q`
- Result: **44 passed**
- Coverage command: `python -m pytest --cov=app --cov-report=term-missing -q`
- Total coverage: **97%**

## 2) Coverage Highlights

- `app/services/moderation_pipeline.py`: 95%
- `app/services/rule_engine.py`: 98%
- `app/services/decision_engine.py`: 98%
- `app/services/rating_service.py`: 89%
- `app/sockets/chat.py`: 97%
- `app/routes/messages.py`: 100%
- `app/routes/moderation.py`: 99%
- `app/routes/admin.py`: 96%
- `app/routes/auth.py`: 94%

## 3) Pipeline Analysis

Validated end-to-end behavior of the moderation pipeline:

1. Access stage:
   - blocked user is rejected before processing (`status=blocked`, no message persistence).
2. Normalization + Rules:
   - length, flood, duplicate, stopwords, link heuristics, repeated symbols are verified.
3. ML stage:
   - ML is skipped when Rule Engine returns `BLOCK`.
   - fallback and error paths of classifier are tested.
4. Decision stage:
   - `ok` / `hidden` / `blocked` transitions are covered, including threshold/rating/shadow-ban branches.
5. Persistence + violations:
   - messages and violations are written with correct status and violation types.
6. Rating & sanctions:
   - rating update formula, warning accumulation, shadow-ban activation, temp block at `warnings>=3` verified.
7. Delivery stage (Socket.IO):
   - `new_message`, `message_blocked`, `message_hidden`, `message_updated` events validated.

## 4) PRD T1-T10 Mapping

- T1 Neutral message -> PASS
- T2 Toxic/direct insult -> PASS
- T3 Flood -> PASS
- T4 Duplicate in window -> PASS
- T5 URL/link handling -> PASS
- T6 Borderline aggression (`hidden`) -> PASS
- T7 `rating > 0.8` escalation -> PASS
- T8 Moderator approve hidden -> PASS
- T9 Admin threshold update affects next decisions -> PASS
- T10 3 violations -> temp block 24h logic -> PASS

## 5) Additional Note

- Fixed a defect in `POST /api/auth/revoke`: endpoint now requires JWT (`@jwt_required(verify_type=False)`) and is covered by tests.

