import math
from collections import Counter
from collections.abc import Callable

import numpy as np
import pandas as pd


def calculate_benfords_law_score(data: list[float]) -> float:
    """
    Calculates the Benford's Law deviation score for a set of numbers.
    A higher score indicates more potential manipulation.
    """
    if not data:
        return 0.0

    first_digits = [int(str(abs(x)).lstrip("0.")[0]) for x in data if x != 0]
    if not first_digits:
        return 0.0

    counts = Counter(first_digits)
    total = len(first_digits)

    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}

    abs_diff = 0.0
    for d in range(1, 10):
        actual_prob = counts.get(d, 0) / total
        abs_diff += abs(actual_prob - expected[d])

    return abs_diff / 9.0


def perform_sequence_analysis(timestamps: list[float], amounts: list[float]) -> dict:
    """
    Analyzes the rhythm and order of transactions.
    Identifies mechanical/bot-like patterns.
    """
    if len(timestamps) < 2:
        return {"rhythm_score": 0.0, "entropy": 0.0}

    deltas = np.diff(timestamps)
    cv = np.std(deltas) / np.mean(deltas) if np.mean(deltas) > 0 else 0

    return {
        "regularity": 1.0 - min(cv, 1.0),
        "avg_delta": float(np.mean(deltas)),
        "std_delta": float(np.std(deltas)),
    }


def eval_fraud_triangle(pressure: float, opportunity: float, rationalization: float) -> float:
    """
    Simple model for the Fraud Triangle: Pressure, Opportunity, Rationalization.
    Returns a combined probability score.
    """
    return (pressure * 0.4) + (opportunity * 0.5) + (rationalization * 0.1)


def detect_time_series_anomalies(
    values: list[float], window_size: int = 10, z_threshold: float = 3.0
) -> dict:
    """
    Detects temporal anomalies using rolling z-score analysis.
    Identifies spikes and dips that deviate from local patterns.
    """
    if len(values) < window_size:
        return {"anomalies": [], "anomaly_count": 0}

    arr = np.array(values)
    anomalies = []
    rolling_mean = []
    rolling_std = []

    for i in range(len(arr) - window_size + 1):
        window = arr[i : i + window_size]
        rolling_mean.append(np.mean(window))
        rolling_std.append(np.std(window))

    for i in range(len(arr)):
        if i < window_size // 2 or i >= len(arr) - window_size // 2:
            continue

        mean = rolling_mean[i - window_size // 2]
        std = rolling_std[i - window_size // 2]

        if std > 0:
            z_score = abs(arr[i] - mean) / std
            if z_score > z_threshold:
                anomalies.append(
                    {
                        "index": i,
                        "value": float(arr[i]),
                        "z_score": float(z_score),
                        "type": "spike" if arr[i] > mean else "dip",
                    }
                )

    return {"anomalies": anomalies, "anomaly_count": len(anomalies), "total_points": len(values)}


def calculate_wallet_risk_score(
    transaction_velocity: float,
    avg_amount: float,
    peer_interactions: int,
    anomaly_count: int,
    age_days: float | None = None,
) -> dict:
    """
    Composite risk score for a wallet based on multiple factors.
    """
    velocity_score = min(transaction_velocity / 100, 1.0)

    amount_score = 0.5
    if avg_amount > 10000:
        amount_score = 0.8
    elif avg_amount > 1000:
        amount_score = 0.6

    peer_score = min(peer_interactions / 50, 1.0)

    anomaly_score = min(anomaly_count / 10, 1.0)

    age_score = 0.5
    if age_days is not None:
        if age_days < 7:
            age_score = 0.9
        elif age_days < 30:
            age_score = 0.7

    overall = (
        velocity_score * 0.25
        + amount_score * 0.2
        + peer_score * 0.15
        + anomaly_score * 0.3
        + age_score * 0.1
    )

    risk_level = "low"
    if overall > 0.7:
        risk_level = "critical"
    elif overall > 0.5:
        risk_level = "high"
    elif overall > 0.3:
        risk_level = "medium"

    return {
        "overall_score": round(overall, 3),
        "risk_level": risk_level,
        "components": {
            "velocity": round(velocity_score, 3),
            "amount": round(amount_score, 3),
            "peers": round(peer_score, 3),
            "anomalies": round(anomaly_score, 3),
            "age": round(age_score, 3),
        },
    }


def analyze_multi_asset(transactions: list[dict], asset_type_field: str = "asset_type") -> dict:
    """
    Analyzes transactions across multiple asset types (ERC-20, NFT, ETH, etc.).
    """
    df = pd.DataFrame(transactions)

    if asset_type_field not in df.columns:
        return {"error": f"Field {asset_type_field} not found"}

    asset_summary = {}
    for asset_type, group in df.groupby(asset_type_field):
        amounts = group["amount"].tolist()
        asset_summary[asset_type] = {
            "count": len(group),
            "total_volume": float(group["amount"].sum()),
            "avg_amount": float(group["amount"].mean()),
            "unique_senders": int(group["source_wallet"].nunique()),
            "unique_receivers": int(group["target_wallet"].nunique()),
            "benford_score": calculate_benfords_law_score(amounts),
        }

    return asset_summary


class AlertRule:
    """Configurable alerting rule for financial monitoring."""

    def __init__(
        self,
        name: str,
        condition_fn: Callable[[dict], bool],
        severity: str = "medium",
        description: str = "",
    ):
        self.name = name
        self.condition_fn = condition_fn
        self.severity = severity
        self.description = description

    def evaluate(self, context: dict) -> bool:
        return self.condition_fn(context)

    def to_dict(self) -> dict:
        return {"name": self.name, "severity": self.severity, "description": self.description}


def create_default_alert_rules() -> list[AlertRule]:
    """Creates default alert rules for financial forensics."""
    return [
        AlertRule(
            name="high_benford_deviation",
            condition_fn=lambda ctx: ctx.get("benford_score", 0) > 0.15,
            severity="high",
            description="Benford's Law deviation exceeds threshold",
        ),
        AlertRule(
            name="large_transaction",
            condition_fn=lambda ctx: ctx.get("amount", 0) > 50000,
            severity="medium",
            description="Single transaction exceeds $50K",
        ),
        AlertRule(
            name="high_velocity",
            condition_fn=lambda ctx: ctx.get("tx_per_hour", 0) > 100,
            severity="high",
            description="Transaction velocity exceeds 100/hour",
        ),
        AlertRule(
            name="new_wallet_large_transfer",
            condition_fn=lambda ctx: (
                ctx.get("wallet_age_days", 999) < 7 and ctx.get("amount", 0) > 10000
            ),
            severity="critical",
            description="New wallet with large transfer",
        ),
        AlertRule(
            name="community_circle",
            condition_fn=lambda ctx: ctx.get("peer_count", 0) > 30,
            severity="low",
            description="Large peer network detected",
        ),
    ]


def evaluate_alert_rules(context: dict, rules: list[AlertRule] | None = None) -> list[dict]:
    """Evaluate all alert rules against context."""
    if rules is None:
        rules = create_default_alert_rules()

    triggered = []
    for rule in rules:
        if rule.evaluate(context):
            triggered.append(rule.to_dict())

    return triggered
