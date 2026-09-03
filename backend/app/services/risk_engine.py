"""Risk engine controls for exposure, sizing, and drawdown protection."""

def position_size(balance: float, risk_percent: float, stop_distance: float) -> float:
    risk_capital = balance * risk_percent
    return risk_capital / max(stop_distance, 1e-8)


def breach_drawdown(equity_peak: float, equity_now: float, max_drawdown: float) -> bool:
    dd = (equity_peak - equity_now) / max(equity_peak, 1e-8)
    return dd >= max_drawdown
