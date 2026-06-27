import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ToxicityClassifier:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._pipe = None
        self._is_ready = False
        self._init_pipeline()

    def _init_pipeline(self) -> None:
        if self.model_name == "disabled":
            LOGGER.warning("ML classifier disabled by config.")
            return

        try:
            from transformers import pipeline

            self._pipe = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,
                truncation=True,
                max_length=128,
            )
            self._is_ready = True
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to initialize ML model '%s': %s", self.model_name, exc)
            self._pipe = None
            self._is_ready = False

    def score(self, text: str) -> dict[str, Any]:
        if not self._is_ready or self._pipe is None:
            return {"aggregate": 0.0, "labels": {}, "fallback": True}

        try:
            results = self._pipe(text)[0]
            labels = {item["label"]: float(item["score"]) for item in results}
            toxic_labels = {key: value for key, value in labels.items() if key != "non-toxic"}
            aggregate = max(toxic_labels.values()) if toxic_labels else 0.0
            return {"aggregate": float(aggregate), "labels": labels, "fallback": False}
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("ML scoring failed: %s", exc)
            return {"aggregate": 0.0, "labels": {}, "fallback": True, "error": str(exc)}


_classifier: ToxicityClassifier | None = None


def get_classifier(model_name: str) -> ToxicityClassifier:
    global _classifier
    if _classifier is None:
        _classifier = ToxicityClassifier(model_name=model_name)
    return _classifier

