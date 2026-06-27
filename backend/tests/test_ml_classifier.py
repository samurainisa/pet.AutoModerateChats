from app.services.ml_classifier import ToxicityClassifier


def test_ml_classifier_disabled_mode():
    classifier = ToxicityClassifier(model_name="disabled")
    result = classifier.score("hello")
    assert result["aggregate"] == 0.0
    assert result["fallback"] is True

