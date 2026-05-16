"""Modular signal engine primitives for ranking trade setups."""
from dataclasses import dataclass


@dataclass
class SignalScore:
    trend: float
    breakout: float
    volatility: float
    momentum: float
    risk_reward: float

    @property
    def total(self) -> float:
        return (self.trend + self.breakout + self.volatility + self.momentum + self.risk_reward) / 5


def rank_setup(score: SignalScore) -> str:
    if score.total >= 0.75:
        return "A"
    if score.total >= 0.6:
        return "B"
    return "C"
