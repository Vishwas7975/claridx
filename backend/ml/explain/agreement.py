"""Quantify how closely two explanations of the same patient agree."""

from dataclasses import dataclass

import numpy as np
from scipy.stats import spearmanr

from ml.explain.types import Explanation


@dataclass(frozen=True)
class Agreement:
    rank_correlation: float | None  # Spearman on |contribution|; None if undefined
    top_k_overlap: float  # share of the top-k features both methods name
    sign_agreement: float  # among the first method's top-k, share with the same direction
    k: int


def compare(first: Explanation, second: Explanation, k: int = 3) -> Agreement:
    a = {item.feature: item.contribution for item in first.contributions}
    b = {item.feature: item.contribution for item in second.contributions}
    if set(a) != set(b):
        raise ValueError("Explanations must cover the same features")

    features = sorted(a)
    abs_a = np.array([abs(a[name]) for name in features])
    abs_b = np.array([abs(b[name]) for name in features])

    rank_correlation = None
    if np.ptp(abs_a) > 0 and np.ptp(abs_b) > 0:
        rank_correlation = float(spearmanr(abs_a, abs_b).statistic)

    top_a = sorted(features, key=lambda name: -abs(a[name]))[:k]
    top_b = sorted(features, key=lambda name: -abs(b[name]))[:k]
    overlap = len(set(top_a) & set(top_b)) / k
    same_sign = float(np.mean([np.sign(a[name]) == np.sign(b[name]) for name in top_a]))

    return Agreement(
        rank_correlation=rank_correlation,
        top_k_overlap=overlap,
        sign_agreement=same_sign,
        k=k,
    )
