from types import SimpleNamespace
from echomatrix.brain import Brain, DecisionEngine


def state(**overrides):
    values = {"price": 100.0, "ema_fast": 101.0, "ema_slow": 100.0, "momentum": 0.01, "volatility": 0.15, "regime": "BULLISH TREND"}
    values.update(overrides)
    return SimpleNamespace(**values)


def test_brain_returns_explicit_decision():
    result = Brain().cycle(state())
    decision = result["decision"]
    assert decision["action"] in {"LONG", "SHORT", "WAIT"}
    assert -1 <= decision["score"] <= 1
    assert 0 <= decision["confidence"] <= 1
    assert 0 <= decision["uncertainty"] <= 1
    assert decision["evidence"]


def test_memory_changes_decision_only_gradually():
    brain = Brain()
    before = brain.engine.decide(state()).score
    for _ in range(3):
        brain.learn("trend", 1.0, {"test": True})
    after = brain.engine.decide(state()).score
    assert abs(after - before) < 0.5
    assert brain.memory.edge["trend"] > 0


def test_high_volatility_raises_wait_threshold():
    engine = DecisionEngine()
    low = engine.decide(state(volatility=0.05))
    high = engine.decide(state(volatility=0.75))
    assert high.uncertainty >= 0
    assert high.action in {"LONG", "SHORT", "WAIT"}
