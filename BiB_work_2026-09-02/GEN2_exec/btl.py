"""Deterministic Bradley-Terry-Luce (BTL) ranking via Hunter's MM algorithm.

Implements the pairwise-comparison aggregation required by the frozen
pre-registration (section 9.3):

    "Deterministic Hunter minorization-maximisation in Python (`choix` or
    in-repo implementation with documented convergence criterion and random
    restarts); LLMs never perform arithmetic aggregation; LLM outputs enter
    only the verdict table. The implementation and its unit tests ship with
    the deposit."

Pure Python 3 standard library (no numpy/scipy), so the deposit reproduces on
a bare CPython install.

Model
-----
Each item i has strength s_i = exp(l_i); the probability that i beats j is

    p_ij = s_i / (s_i + s_j) = 1 / (1 + exp(l_j - l_i)).

Algorithm (Hunter 2004, minorization-maximization)
--------------------------------------------------
With W_i the total win credit of item i (a tie credits 0.5 to each side) and
n_ij the number of comparisons between i and j, every sweep updates each
log-strength from the previous sweep's vector (Jacobi updates):

    l_i_new = log(W_i + eps) - log( sum_{j != i} n_ij / (exp(l_i) + exp(l_j)) )

After each sweep the log-strength vector is re-centred to mean zero, so the
strengths of the compared items have geometric mean 1.  The model is invariant
under this rescaling; centring keeps exp() well conditioned.

Convergence criterion (documented per the pre-registration): iteration stops
when the maximum absolute change of any centred log-strength between
consecutive sweeps falls below `tol`,

    max_i | l_i^(t) - l_i^(t-1) | < tol          (default tol = 1e-10),

or when `max_iter` sweeps have run, in which case "converged" is False.  For
decisive (non-strongly-connected) verdict tables the exact BT maximum
likelihood does not exist, the likelihood is nearly flat along a ridge, and
the log-strength iterate crawls: such inputs may legitimately exhaust
`max_iter` with the correct ranking and near-1 decisive probabilities already
in hand.  Real split-verdict tournaments (wins and losses on every item) are
strongly connected and converge quickly.

Regularisation guard
--------------------
eps = 1e-12 pseudo-wins are added to every item's win credit.  Without the
guard, an item that wins or loses every comparison has no finite MLE
(strength +inf or 0), and a winless item would make log(W_i) = log(0) raise.
With the guard, decisive pairs are capped near p = 1 - 1e-12 and winless items
keep small positive strengths; for items with at least one win and one loss
the bias is below ~1e-12 in probability, far under reporting precision.

Determinism
-----------
Output is bit-for-bit reproducible: no wall-clock, randomness, or hash-order
dependence.  Extra starts (restarts > 1) draw their initial log-strength
perturbations from random.Random(PERM_SEED) with the frozen pre-registration
seed 20260101; the all-zero start always runs first and wins exact
log-likelihood ties, so tie-breaking is itself deterministic.

References
----------
- Bradley, R. A. and Terry, M. E. (1952). Rank analysis of incomplete block
  designs: the method of paired comparisons. Biometrika 39(3-4), 324-345.
- Hunter, D. R. (2004). MM algorithms for generalized Bradley-Terry models.
  The Annals of Statistics 32(1).
- Luce, R. D. (1959). "Individual Choice Behavior." Wiley, New York.
"""

import math
import random

__all__ = ["fit_btl", "top_k", "PERM_SEED"]

#: Frozen pre-registration permutation seed; all randomness flows from it.
PERM_SEED = 20260101

#: Pseudo-win count added to every item's win credit (regularisation guard).
_EPS = 1e-12


# ---------------------------------------------------------------------------
# Numerically stable primitives
# ---------------------------------------------------------------------------

def _log_denom(i, log_str, counts):
    """log( sum_{j != i} n_ij / (exp(l_i) + exp(l_j)) ), overflow-safe.

    Each summand is evaluated in log space as log(n_ij) - logsumexp(l_i, l_j),
    so every exponential has a non-positive argument no matter how far apart
    the log-strengths have spread.
    """
    li = log_str[i]
    terms = []
    for j, n_ij in enumerate(counts[i]):
        if j == i or n_ij <= 0:
            continue
        lj = log_str[j]
        top = li if li > lj else lj
        log_sum = top + math.log1p(math.exp(-abs(li - lj)))
        terms.append(math.log(n_ij) - log_sum)
    peak = max(terms)
    return peak + math.log(sum(math.exp(t - peak) for t in terms))


def _log_sigmoid(x):
    """log( 1 / (1 + exp(-x)) ), stable for large |x|."""
    if x >= 0.0:
        return -math.log1p(math.exp(-x))
    return x - math.log1p(math.exp(x))


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def _parse_pairs(pairs, n_items, item_names):
    """Normalise the verdict list into labels and count matrices.

    Returns (labels, counts, credits):
      labels  -- list of item keys (strings or ints); position is the
                 internal index
      counts  -- n x n int matrix; counts[i][j] = number of i-vs-j
                 comparisons (symmetric)
      credits -- n x n float matrix; credits[i][j] = win credit i earned
                 against j (1.0 per win, 0.5 per tie)
    """
    seq = list(pairs)
    for entry in seq:
        if not isinstance(entry, (list, tuple)):
            raise TypeError("each comparison must be a tuple or list")
        if len(entry) not in (2, 3):
            raise ValueError(
                "each comparison must be (winner, loser) or (a, b, 'tie')")
        if len(entry) == 3 and entry[2] != "tie":
            raise ValueError("the third field of a comparison must be 'tie'")

    elems = [entry[k] for entry in seq for k in (0, 1)]
    string_items = bool(elems) and isinstance(elems[0], str)
    for x in elems:
        if isinstance(x, bool) or not isinstance(x, (str, int)):
            raise TypeError("item identifiers must be strings or integers")
        if isinstance(x, str) != string_items:
            raise ValueError(
                "all item identifiers in `pairs` must have the same type")

    if item_names is not None:
        labels = list(item_names)
        if len(set(labels)) != len(labels):
            raise ValueError("item_names must be unique")
        n = len(labels)
        if n_items is not None and n_items != n:
            raise ValueError("n_items conflicts with len(item_names)")
        if string_items:
            known = set(labels)
            for x in elems:
                if x not in known:
                    raise ValueError("unknown item name: %r" % (x,))
        else:
            for idx in elems:
                if not 0 <= idx < n:
                    raise ValueError(
                        "item index %r out of range [0, %d)" % (idx, n))
    elif string_items:
        labels = []
        seen = set()
        for x in elems:
            if x not in seen:
                seen.add(x)
                labels.append(x)
        n = len(labels)
        if n_items is not None and n_items != n:
            raise ValueError(
                "n_items does not match the distinct names in `pairs`; pass "
                "item_names to declare items with zero comparisons")
    else:
        n = int(n_items) if n_items is not None else (
            max(elems) + 1 if elems else 0)
        labels = list(range(n))
        for idx in elems:
            if not 0 <= idx < n:
                raise ValueError(
                    "item index %r out of range [0, %d)" % (idx, n))

    index = {label: i for i, label in enumerate(labels)} \
        if string_items else None

    counts = [[0] * n for _ in range(n)]
    credits = [[0.0] * n for _ in range(n)]
    for entry in seq:
        ia = index[entry[0]] if index is not None else entry[0]
        ib = index[entry[1]] if index is not None else entry[1]
        if ia == ib:
            raise ValueError(
                "an item cannot be compared with itself: %r" % (entry[0],))
        counts[ia][ib] += 1
        counts[ib][ia] += 1
        if len(entry) == 3:
            credits[ia][ib] += 0.5
            credits[ib][ia] += 0.5
        else:
            credits[ia][ib] += 1.0
    return labels, counts, credits


# ---------------------------------------------------------------------------
# Core MM iteration
# ---------------------------------------------------------------------------

def _fit_core(wins, counts, l0, max_iter, tol):
    """Run MM sweeps on the compared subset from one starting point.

    wins[i] is the total win credit of item i (ties counted as 0.5).  Returns
    (log_strengths, converged, iterations); log_strengths are centred to mean
    zero.  The convergence criterion is max_i |l_i_new - l_i_old| < tol on
    the centred vector (see module docstring).
    """
    m = len(wins)
    log_w = [math.log(w + _EPS) for w in wins]
    shift = sum(l0) / m
    l = [x - shift for x in l0]
    converged = False
    iterations = 0
    for iterations in range(1, max_iter + 1):
        new = [log_w[i] - _log_denom(i, l, counts) for i in range(m)]
        shift = sum(new) / m
        new = [x - shift for x in new]
        delta = max(abs(new[i] - l[i]) for i in range(m))
        l = new
        if delta < tol:
            converged = True
            break
    return l, converged, iterations


def _pairwise_loglik(log_str, credits):
    """Bradley-Terry log-likelihood of the tie-credited verdicts at log_str.

    Summed over unordered pairs: credit_i * log(p_ij) + credit_j * log(p_ji).
    The eps pseudo-win guard is a fitting device only and is not part of the
    reported objective.
    """
    total = 0.0
    m = len(log_str)
    for i in range(m):
        for j in range(i + 1, m):
            c_ij = credits[i][j]
            c_ji = credits[j][i]
            if c_ij <= 0.0 and c_ji <= 0.0:
                continue
            d = log_str[i] - log_str[j]
            if c_ij > 0.0:
                total += c_ij * _log_sigmoid(d)
            if c_ji > 0.0:
                total += c_ji * _log_sigmoid(-d)
    return total


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fit_btl(pairs, n_items=None, item_names=None, max_iter=10000,
            tol=1e-10, restarts=3):
    """Fit Bradley-Terry-Luce strengths to a table of pairwise verdicts.

    Parameters
    ----------
    pairs : sequence of comparisons
        Each comparison is ``(winner, loser)`` or ``(a, b, "tie")``.  Items
        may be strings or integer indices (0-based), but not mixed within a
        call.  A tie credits half a win to each side.
    n_items : int, optional
        Total number of items when integer indices are used; declares items
        that never appear in `pairs`.  Must be consistent with `item_names`
        when both are given.
    item_names : sequence, optional
        Labels for all items, including items with zero comparisons.  When
        items are integer indices, item_names[i] labels item i in the output.
    max_iter : int, optional
        Maximum number of MM sweeps per start (default 10,000).
    tol : float, optional
        Convergence tolerance: iteration stops when the maximum absolute
        change of any centred log-strength between consecutive sweeps drops
        below `tol` (default 1e-10).
    restarts : int, optional
        Number of starts (at least 1; default 3).  Start 0 is the all-zero
        log-strength vector; later starts are seeded perturbations drawn from
        random.Random(PERM_SEED) with PERM_SEED = 20260101, so results are
        bit-for-bit reproducible.  The start with the highest log-likelihood
        is returned; exact ties keep the earlier start.

    Returns
    -------
    dict with keys
        "strengths"  : {item: float or None}.  s_i = exp(l_i); compared items
                       have geometric mean 1.  None for items with zero
                       comparisons.
        "ranking"    : items sorted by descending strength; equal strengths
                       are broken deterministically by declaration /
                       first-appearance order; zero-comparison items are
                       excluded.
        "n_items"    : total number of items, including zero-comparison ones.
        "converged"  : whether the returned fit met the tolerance within
                       `max_iter` sweeps.
        "iterations" : MM sweeps used by the returned fit.
        "loglik"     : Bradley-Terry log-likelihood of the tie-credited data
                       at the fitted strengths (higher is better).
    """
    labels, counts, credits = _parse_pairs(pairs, n_items, item_names)
    n = len(labels)
    wins_full = [sum(row) for row in credits]
    # Items are fittable when they were compared at least once (a winless
    # but played item is ranked, at the bottom; only unplayed items are
    # excluded).
    compared = [i for i in range(n) if sum(counts[i]) > 0]

    strengths = {label: None for label in labels}
    if not compared:
        return {"strengths": strengths, "ranking": [], "n_items": n,
                "converged": True, "iterations": 0, "loglik": 0.0}

    sub_counts = [[counts[i][j] for j in compared] for i in compared]
    sub_credits = [[credits[i][j] for j in compared] for i in compared]
    sub_wins = [wins_full[i] for i in compared]
    m = len(compared)

    max_iter = max(1, int(max_iter))
    rng = random.Random(PERM_SEED)
    best = None
    for start in range(max(1, int(restarts))):
        if start == 0:
            l0 = [0.0] * m
        else:
            l0 = [rng.uniform(-1.0, 1.0) for _ in range(m)]
        log_str, converged, iterations = _fit_core(
            sub_wins, sub_counts, l0, max_iter, tol)
        loglik = _pairwise_loglik(log_str, sub_credits)
        if best is None or loglik > best[0]:
            best = (loglik, log_str, converged, iterations)
    loglik, log_str, converged, iterations = best

    fitted = {}
    for k, i in enumerate(compared):
        fitted[i] = math.exp(log_str[k])
        strengths[labels[i]] = fitted[i]
    ranking = [labels[i] for i in sorted(compared, key=lambda i: -fitted[i])]

    return {"strengths": strengths, "ranking": ranking, "n_items": n,
            "converged": converged, "iterations": iterations,
            "loglik": loglik}


def top_k(pairs, k=5, **kwargs):
    """Fit BTL (arguments as for `fit_btl`) and return the top-k item names
    by strength, in descending order."""
    return fit_btl(pairs, **kwargs)["ranking"][:k]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    """Fit a small seeded synthetic tournament and print the ranking."""
    rng = random.Random(PERM_SEED)
    players = ["Atlas", "Boreas", "Calder", "Dorian", "Echo"]
    true_log = {"Atlas": 0.8, "Boreas": 0.4, "Calder": 0.0,
                "Dorian": -0.4, "Echo": -0.8}
    games_per_pair = 6

    pairs = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            d = true_log[players[i]] - true_log[players[j]]
            p = 1.0 / (1.0 + math.exp(-d))
            for _ in range(games_per_pair):
                if rng.random() < p:
                    pairs.append((players[i], players[j]))
                else:
                    pairs.append((players[j], players[i]))

    res = fit_btl(pairs)
    wins = {name: 0 for name in players}
    losses = {name: 0 for name in players}
    for winner, loser in pairs:
        wins[winner] += 1
        losses[loser] += 1

    print("Bradley-Terry-Luce demo: synthetic round-robin, 5 players, "
          "%d games per pair (seed %d)" % (games_per_pair, PERM_SEED))
    print("%-6s %-10s %12s %10s" % ("Rank", "Player", "Strength", "Record"))
    for rank, name in enumerate(res["ranking"], start=1):
        print("%-6d %-10s %12.4f %6d-%-6d"
              % (rank, name, res["strengths"][name], wins[name], losses[name]))
    print("converged=%s  iterations=%d  log-likelihood=%.6f  n_items=%d"
          % (res["converged"], res["iterations"], res["loglik"],
             res["n_items"]))
    print("top 3:", ", ".join(top_k(pairs, k=3)))


if __name__ == "__main__":
    _demo()
