"""
FAERS signal detection module for FDA Adverse Event Reporting System data.

Queries the openFDA API and computes standard pharmacovigilance disproportionality
metrics for approved CAR-T and bispecific antibody products.  Three metrics are
computed for each product-adverse event pair:

    1. PRR  -- Proportional Reporting Ratio (with 95% CI)
    2. ROR  -- Reporting Odds Ratio (with 95% CI)
    3. EBGM -- Empirical Bayesian Geometric Mean (Multi-item Gamma Poisson Shrinker)

Signal strength is classified as none / weak / moderate / strong based on
standard pharmacovigilance thresholds (Evans 2001, Szarfman 2002).

Implements standard pharmacovigilance disproportionality metrics,
refactored as a standalone module with proper MGPS-based EBGM computation.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTTP client -- prefer httpx, fall back to urllib
# ---------------------------------------------------------------------------

try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    import json
    import urllib.request
    import urllib.error
    import urllib.parse

    _HAS_HTTPX = False
    logger.warning(
        "httpx not installed; falling back to urllib for openFDA queries. "
        "Install httpx for async support: pip install httpx"
    )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FAERSSignal:
    """A single disproportionality signal from FAERS data.

    Attributes:
        product: Brand name of the product (e.g. "KYMRIAH").
        adverse_event: MedDRA preferred term for the adverse event.
        n_cases: Number of reports for this drug-AE pair (cell ``a``).
        n_total_product: Total reports for this product (``a + b``).
        n_total_ae: Total reports for this AE across all products (``a + c``).
        n_total_database: Total reports in the FAERS database (``a + b + c + d``).
        prr: Proportional Reporting Ratio.
        prr_ci_low: PRR 95% CI lower bound.
        prr_ci_high: PRR 95% CI upper bound.
        ror: Reporting Odds Ratio.
        ror_ci_low: ROR 95% CI lower bound.
        ror_ci_high: ROR 95% CI upper bound.
        ebgm: Empirical Bayesian Geometric Mean.
        ebgm05: EBGM lower 5th percentile (conservative bound).
        is_signal: True if the pair meets signal detection thresholds.
        signal_strength: One of "none", "weak", "moderate", "strong".
    """

    product: str
    adverse_event: str
    n_cases: int
    n_total_product: int
    n_total_ae: int
    n_total_database: int
    prr: float
    prr_ci_low: float
    prr_ci_high: float
    ror: float
    ror_ci_low: float
    ror_ci_high: float
    ebgm: float
    ebgm05: float
    is_signal: bool
    signal_strength: str


@dataclass
class FAERSSummary:
    """Summary of FAERS analysis for a set of products.

    Attributes:
        products_queried: List of product names that were analysed.
        total_reports: Sum of all reports across queried products.
        signals_detected: Count of product-AE pairs flagged as signals.
        strong_signals: Count of strong signals only.
        signals: List of all FAERSSignal results (including non-signals).
        query_timestamp: ISO-8601 timestamp of when the analysis was run.
    """

    products_queried: list[str]
    total_reports: int
    signals_detected: int
    strong_signals: int
    signals: list[FAERSSignal]
    query_timestamp: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPENFDA_BASE = "https://api.fda.gov/drug/event.json"

# Known CAR-T / bispecific product names for querying FAERS.
# Maps canonical brand name to a list of search terms (brand + generic).
CAR_T_PRODUCTS: dict[str, list[str]] = {
    "KYMRIAH": ["KYMRIAH", "TISAGENLECLEUCEL"],
    "YESCARTA": ["YESCARTA", "AXICABTAGENE CILOLEUCEL"],
    "BREYANZI": ["BREYANZI", "LISOCABTAGENE MARALEUCEL"],
    "ABECMA": ["ABECMA", "IDECABTAGENE VICLEUCEL"],
    "CARVYKTI": ["CARVYKTI", "CILTACABTAGENE AUTOLEUCEL"],
    "TECVAYLI": ["TECVAYLI", "TECLISTAMAB"],
}

# Target adverse events -- MedDRA preferred terms of interest.
TARGET_AES: list[str] = [
    "Cytokine release syndrome",
    "Immune effector cell-associated neurotoxicity syndrome",
    "Neurotoxicity",
    "Encephalopathy",
    "Febrile neutropenia",
    "Pancytopenia",
    "Hypogammaglobulinaemia",
    "Tumour lysis syndrome",
    "Haemophagocytic lymphohistiocytosis",
    "T-cell lymphoma",
]

# Rate limiting: openFDA allows 40 requests/minute without an API key.
_RATE_LIMIT_REQUESTS = 40
_RATE_LIMIT_WINDOW_SECONDS = 60.0
_request_timestamps: list[float] = []

# Simple in-memory cache: key -> (timestamp, data).  24-hour TTL.
_cache: dict[str, tuple[float, object]] = {}
_CACHE_TTL_SECONDS = 86400


# ---------------------------------------------------------------------------
# Caching helpers
# ---------------------------------------------------------------------------

def _cache_get(key: str) -> object | None:
    """Return cached value if still within TTL, else None."""
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: object) -> None:
    """Store value in cache with current timestamp."""
    _cache[key] = (time.time(), data)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

async def _rate_limit() -> None:
    """Enforce openFDA rate limit (40 requests per 60 seconds).

    Blocks until a request slot is available.
    """
    now = time.time()
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS

    # Prune timestamps outside the window
    while _request_timestamps and _request_timestamps[0] < cutoff:
        _request_timestamps.pop(0)

    if len(_request_timestamps) >= _RATE_LIMIT_REQUESTS:
        # Wait until the oldest request in the window expires
        wait_time = _request_timestamps[0] - cutoff + 0.1
        logger.debug("Rate limit hit; sleeping %.2f seconds", wait_time)
        await asyncio.sleep(wait_time)

    _request_timestamps.append(time.time())


# ---------------------------------------------------------------------------
# Core computation functions
# ---------------------------------------------------------------------------

def compute_prr(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    """Compute Proportional Reporting Ratio and 95% CI from a 2x2 table.

    The 2x2 contingency table:

    ================  ==============  ================
                      Target AE       Other AEs
    ================  ==============  ================
    Target drug       a               b
    Other drugs       c               d
    ================  ==============  ================

    Formula::

        PRR = (a / (a + b)) / (c / (c + d))
        SE(ln PRR) = sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
        95% CI = exp(ln(PRR) +/- 1.96 * SE)

    Args:
        a: Cases with target drug AND target event.
        b: Cases with target drug, NOT target event.
        c: Cases without target drug, WITH target event.
        d: Cases without target drug, NOT target event.

    Returns:
        Tuple of (prr, ci_low, ci_high).  Returns (0.0, 0.0, 0.0) if
        computation fails due to zero denominators.
    """
    try:
        if (a + b) == 0 or (c + d) == 0 or c == 0:
            return (0.0, 0.0, 0.0)

        rate_drug = a / (a + b)
        rate_other = c / (c + d)

        if rate_other == 0.0:
            return (0.0, 0.0, 0.0)

        prr = rate_drug / rate_other

        # Confidence interval requires a > 0 for the log transform
        if a <= 0 or prr <= 0.0:
            return (prr, 0.0, 0.0)

        se_ln_prr = math.sqrt(
            (1 / a) - (1 / (a + b)) + (1 / c) - (1 / (c + d))
        )
        ln_prr = math.log(prr)
        ci_low = math.exp(ln_prr - 1.96 * se_ln_prr)
        ci_high = math.exp(ln_prr + 1.96 * se_ln_prr)

        return (prr, ci_low, ci_high)

    except (ValueError, ZeroDivisionError, OverflowError):
        return (0.0, 0.0, 0.0)


def compute_ror(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    """Compute Reporting Odds Ratio and 95% CI from a 2x2 table.

    Formula::

        ROR = (a * d) / (b * c)
        SE(ln ROR) = sqrt(1/a + 1/b + 1/c + 1/d)
        95% CI = exp(ln(ROR) +/- 1.96 * SE)

    Args:
        a: Cases with target drug AND target event.
        b: Cases with target drug, NOT target event.
        c: Cases without target drug, WITH target event.
        d: Cases without target drug, NOT target event.

    Returns:
        Tuple of (ror, ci_low, ci_high).  Returns (0.0, 0.0, 0.0) if
        computation fails.
    """
    try:
        if b == 0 or c == 0:
            return (0.0, 0.0, 0.0)

        ror = (a * d) / (b * c)

        if a <= 0 or d <= 0 or ror <= 0.0:
            return (ror, 0.0, 0.0)

        se_ln_ror = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        ln_ror = math.log(ror)
        ci_low = math.exp(ln_ror - 1.96 * se_ln_ror)
        ci_high = math.exp(ln_ror + 1.96 * se_ln_ror)

        return (ror, ci_low, ci_high)

    except (ValueError, ZeroDivisionError, OverflowError):
        return (0.0, 0.0, 0.0)


def compute_ebgm(
    observed: int,
    expected: float,
    alpha1: float = 0.2,
    beta1: float = 0.1,
    alpha2: float = 2.0,
    beta2: float = 4.0,
    p: float = 1 / 3,
) -> tuple[float, float]:
    """Compute EBGM and EBGM05 using Multi-item Gamma Poisson Shrinker.

    Implements the GPS (Gamma Poisson Shrinker) model from DuMouchel (1999).
    The prior on the Poisson rate lambda is a mixture of two Gamma distributions:

        pi(lambda) = p * Gamma(alpha1, beta1) + (1-p) * Gamma(alpha2, beta2)

    The posterior is also a mixture of two Gammas.  The EBGM is the geometric
    mean of the posterior distribution.  EBGM05 is the 5th percentile,
    providing a conservative lower bound.

    The EBGM is computed as::

        E[ln(lambda) | n, E] for each component, weighted by posterior
        component probabilities, then exponentiated.

    Args:
        observed: Observed count (n) for the drug-event pair.
        expected: Expected count (E) under independence assumption.
        alpha1: Shape parameter for the first Gamma component.
        beta1: Rate parameter for the first Gamma component.
        alpha2: Shape parameter for the second Gamma component.
        beta2: Rate parameter for the second Gamma component.
        p: Prior mixing weight for the first component.

    Returns:
        Tuple of (ebgm, ebgm05).  Returns (0.0, 0.0) if expected <= 0 or
        computation fails.
    """
    try:
        if expected <= 0.0 or observed < 0:
            return (0.0, 0.0)

        n = observed
        E = expected

        # Posterior parameters for each Gamma component
        # Component k: Gamma(alpha_k + n, beta_k + E)
        a1_post = alpha1 + n
        b1_post = beta1 + E
        a2_post = alpha2 + n
        b2_post = beta2 + E

        # Log-marginal likelihood for each component (Negative Binomial)
        # log P(n | component k) = log Gamma(alpha_k + n) - log Gamma(alpha_k)
        #     + alpha_k * log(beta_k) - (alpha_k + n) * log(beta_k + E)
        #     - log(n!)
        log_ml1 = (
            math.lgamma(a1_post) - math.lgamma(alpha1)
            + alpha1 * math.log(beta1) - a1_post * math.log(b1_post)
            - math.lgamma(n + 1)
        )
        log_ml2 = (
            math.lgamma(a2_post) - math.lgamma(alpha2)
            + alpha2 * math.log(beta2) - a2_post * math.log(b2_post)
            - math.lgamma(n + 1)
        )

        # Posterior mixing weights (via log-sum-exp for numerical stability)
        log_w1 = math.log(p) + log_ml1
        log_w2 = math.log(1 - p) + log_ml2
        log_w_max = max(log_w1, log_w2)

        w1 = math.exp(log_w1 - log_w_max)
        w2 = math.exp(log_w2 - log_w_max)
        w_total = w1 + w2

        q1 = w1 / w_total  # posterior weight for component 1
        q2 = w2 / w_total  # posterior weight for component 2

        # EBGM = exp(E[ln lambda | data])
        # For Gamma(a, b), E[ln X] = digamma(a) - ln(b)
        eln1 = _digamma(a1_post) - math.log(b1_post)
        eln2 = _digamma(a2_post) - math.log(b2_post)

        e_ln_lambda = q1 * eln1 + q2 * eln2
        ebgm = math.exp(e_ln_lambda)

        # EBGM05 -- 5th percentile of the posterior mixture
        # Approximate using the weighted quantile approach.
        # For each Gamma component, the 5th percentile can be approximated
        # using the Wilson-Hilferty normal approximation to the Gamma quantile.
        q05_1 = _gamma_quantile_approx(a1_post, b1_post, 0.05)
        q05_2 = _gamma_quantile_approx(a2_post, b2_post, 0.05)

        # Weighted 5th percentile (conservative: use the lower of the two
        # weighted quantiles as a simple bound)
        ebgm05 = q1 * q05_1 + q2 * q05_2

        return (ebgm, ebgm05)

    except (ValueError, ZeroDivisionError, OverflowError):
        return (0.0, 0.0)


def _digamma(x: float) -> float:
    """Compute the digamma function psi(x) using Stirling's asymptotic series.

    For x >= 6, uses the asymptotic expansion.  For x < 6, uses the
    recurrence relation psi(x) = psi(x+1) - 1/x to shift x upward.

    Accurate to approximately 10 decimal places for x > 0.
    """
    if x <= 0.0:
        raise ValueError(f"digamma requires x > 0, got {x}")

    result = 0.0
    # Use recurrence to shift x >= 6
    while x < 6.0:
        result -= 1.0 / x
        x += 1.0

    # Asymptotic expansion (Abramowitz & Stegun 6.3.18)
    x2 = 1.0 / (x * x)
    result += (
        math.log(x)
        - 0.5 / x
        - x2
        * (
            1.0 / 12
            - x2
            * (
                1.0 / 120
                - x2 * (1.0 / 252 - x2 * (1.0 / 240 - x2 * (1.0 / 132)))
            )
        )
    )
    return result


def _gamma_quantile_approx(shape: float, rate: float, p: float) -> float:
    """Approximate quantile of Gamma(shape, rate) at probability p.

    Uses the Wilson-Hilferty cube-root normal approximation::

        X ~ Gamma(a, b)
        Q_p(X) approx (a/b) * (1 - 1/(9a) + z_p * sqrt(1/(9a)))^3

    where z_p is the standard normal quantile at probability p.

    Args:
        shape: Shape parameter (alpha) of the Gamma distribution.
        rate: Rate parameter (beta) of the Gamma distribution.
        p: Probability level (e.g. 0.05 for 5th percentile).

    Returns:
        Approximate quantile value.  Returns 0.0 if shape or rate is non-positive.
    """
    if shape <= 0.0 or rate <= 0.0:
        return 0.0

    z_p = _normal_quantile(p)
    v = 1.0 / (9.0 * shape)
    cube = 1.0 - v + z_p * math.sqrt(v)

    if cube <= 0.0:
        return 0.0

    return max(0.0, (shape / rate) * cube ** 3)


def _normal_quantile(p: float) -> float:
    """Approximate the standard normal quantile (inverse CDF).

    Uses the rational approximation from Abramowitz & Stegun (formula 26.2.23),
    accurate to about 4.5 x 10^-4.

    Args:
        p: Probability in (0, 1).

    Returns:
        z such that Phi(z) = p, where Phi is the standard normal CDF.
    """
    if p <= 0.0 or p >= 1.0:
        raise ValueError(f"p must be in (0, 1), got {p}")

    if p > 0.5:
        return -_normal_quantile(1.0 - p)

    # Abramowitz & Stegun constants
    t = math.sqrt(-2.0 * math.log(p))
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t ** 3)
    return -z


def classify_signal(
    prr: float,
    prr_ci_low: float,
    ror: float,
    ror_ci_low: float,
    ebgm05: float,
    n_cases: int,
) -> tuple[bool, str]:
    """Classify signal strength based on standard pharmacovigilance criteria.

    Applies a tiered classification:

    - **Strong**: PRR >= 2 AND PRR CI_low > 1 AND n_cases >= 3 AND EBGM05 >= 2
    - **Moderate**: PRR >= 2 AND ROR CI_low > 1 AND n_cases >= 3
    - **Weak**: PRR >= 1.5 OR EBGM05 >= 1
    - **None**: Below all thresholds

    These thresholds are based on Evans et al. (2001) for PRR/ROR and
    Szarfman et al. (2002) / DuMouchel (1999) for EBGM criteria.

    Args:
        prr: Proportional Reporting Ratio.
        prr_ci_low: PRR 95% CI lower bound.
        ror: Reporting Odds Ratio.
        ror_ci_low: ROR 95% CI lower bound.
        ebgm05: EBGM 5th percentile (lower bound).
        n_cases: Number of drug-AE pair reports.

    Returns:
        Tuple of (is_signal, strength) where is_signal is True for any
        non-"none" strength.
    """
    # Strong signal
    if prr >= 2.0 and prr_ci_low > 1.0 and n_cases >= 3 and ebgm05 >= 2.0:
        return (True, "strong")

    # Moderate signal
    if prr >= 2.0 and ror_ci_low > 1.0 and n_cases >= 3:
        return (True, "moderate")

    # Weak signal
    if prr >= 1.5 or ebgm05 >= 1.0:
        return (True, "weak")

    return (False, "none")


# ---------------------------------------------------------------------------
# openFDA API integration
# ---------------------------------------------------------------------------

async def _http_get_json(url: str, params: dict[str, str]) -> dict:
    """Make an HTTP GET request and return parsed JSON.

    Uses httpx if available, otherwise falls back to urllib.
    Includes rate limiting for the openFDA API.

    Args:
        url: Base URL.
        params: Query parameters.

    Returns:
        Parsed JSON response as a dict.  Returns empty dict on error.
    """
    await _rate_limit()

    if _HAS_HTTPX:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    logger.debug("openFDA 404 for params %s", params)
                    return {}
                else:
                    logger.warning(
                        "openFDA returned %d: %s",
                        resp.status_code,
                        resp.text[:200],
                    )
                    return {}
        except Exception:
            logger.exception("HTTP request to openFDA failed")
            return {}
    else:
        # Synchronous urllib fallback
        try:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode())
                return {}
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {}
            logger.warning("openFDA urllib error %d", exc.code)
            return {}
        except Exception:
            logger.exception("urllib request to openFDA failed")
            return {}


async def query_openfda(
    product_names: list[str],
    adverse_event: str,
    limit: int = 100,
) -> dict:
    """Query the openFDA FAERS API for a specific product-AE combination.

    Builds an openFDA query using the brand_name field and reaction MedDRA
    preferred term.  Tries each product name variant (brand and generic)
    until a result is found.

    The query format is::

        search=patient.drug.openfda.brand_name:"PRODUCT"
               +AND+patient.reaction.reactionmeddrapt:"AE"

    Args:
        product_names: List of name variants for the product (e.g.
            ``["KYMRIAH", "TISAGENLECLEUCEL"]``).
        adverse_event: MedDRA preferred term (e.g. "Cytokine release syndrome").
        limit: Maximum number of results to return.

    Returns:
        Parsed JSON response from openFDA, or empty dict on error / no results.
    """
    for name in product_names:
        search = (
            f'patient.drug.openfda.brand_name:"{name}"'
            f'+AND+patient.reaction.reactionmeddrapt:"{adverse_event}"'
        )
        params = {
            "search": search,
            "limit": str(limit),
        }
        data = await _http_get_json(OPENFDA_BASE, params)
        if data:
            return data

    return {}


async def _get_total_product_reports(product_names: list[str]) -> int:
    """Get total FAERS reports for a product (tries all name variants).

    Args:
        product_names: List of name variants.

    Returns:
        Total report count, or 0 if not found.
    """
    cache_key = f"faers_total_{'_'.join(product_names)}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    for name in product_names:
        params = {
            "search": f'patient.drug.openfda.brand_name:"{name}"',
            "limit": "1",
        }
        data = await _http_get_json(OPENFDA_BASE, params)
        if data:
            total = data.get("meta", {}).get("results", {}).get("total", 0)
            if total > 0:
                _cache_set(cache_key, total)
                return total

    return 0


async def _get_total_ae_reports(adverse_event: str) -> int:
    """Get total FAERS reports for a specific AE across all drugs.

    Args:
        adverse_event: MedDRA preferred term.

    Returns:
        Total report count, or 0 if not found.
    """
    cache_key = f"faers_ae_{adverse_event}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    params = {
        "search": f'patient.reaction.reactionmeddrapt:"{adverse_event}"',
        "limit": "1",
    }
    data = await _http_get_json(OPENFDA_BASE, params)
    if data:
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        _cache_set(cache_key, total)
        return total

    return 0


async def _get_total_database_reports() -> int:
    """Get approximate total FAERS database size.

    Queries a very common reaction (NAUSEA) and extrapolates from its total
    to estimate the full database size.  The true FAERS database contains
    ~30 million reports.

    Returns:
        Estimated total report count.  Falls back to 20,000,000 on error.
    """
    cache_key = "faers_total_database"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    params = {
        "search": 'patient.reaction.reactionmeddrapt:"NAUSEA"',
        "limit": "1",
    }
    data = await _http_get_json(OPENFDA_BASE, params)
    if data:
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        # Use a conservative multiplier; NAUSEA covers ~1/10 of all reports
        estimated_total = max(total * 10, 20_000_000)
        _cache_set(cache_key, estimated_total)
        return estimated_total

    return 20_000_000  # fallback


async def _get_drug_ae_count(
    product_names: list[str],
    adverse_event: str,
) -> int:
    """Get the count of reports for a specific drug-AE pair.

    Args:
        product_names: List of name variants for the product.
        adverse_event: MedDRA preferred term.

    Returns:
        Report count (cell ``a`` of the 2x2 table).
    """
    data = await query_openfda(product_names, adverse_event, limit=1)
    if data:
        return data.get("meta", {}).get("results", {}).get("total", 0)
    return 0


async def get_faers_signals(
    products: list[str] | None = None,
) -> FAERSSummary:
    """Run full FAERS signal detection for specified CAR-T products.

    For each product-AE pair:
        1. Query openFDA for the 2x2 table counts.
        2. Compute PRR, ROR, and EBGM.
        3. Classify signal strength.
        4. Collect into an FAERSSummary.

    Args:
        products: List of product brand names to query (keys from
            ``CAR_T_PRODUCTS``).  If None, queries all known products.

    Returns:
        FAERSSummary containing all signal results, sorted with detected
        signals first and then by PRR descending.
    """
    if products is None:
        products_to_query = list(CAR_T_PRODUCTS.keys())
    else:
        # Normalise to uppercase and filter to known products
        products_to_query = []
        for p in products:
            p_upper = p.strip().upper()
            if p_upper in CAR_T_PRODUCTS:
                products_to_query.append(p_upper)
            else:
                # Try matching against generic names
                for brand, names in CAR_T_PRODUCTS.items():
                    if any(p_upper in n.upper() for n in names):
                        products_to_query.append(brand)
                        break
                else:
                    logger.warning("Unknown product '%s'; skipping", p)

        if not products_to_query:
            products_to_query = list(CAR_T_PRODUCTS.keys())

    # Get database-wide total
    n_total_database = await _get_total_database_reports()

    signals: list[FAERSSignal] = []
    total_product_reports = 0

    for brand in products_to_query:
        product_names = CAR_T_PRODUCTS[brand]

        # Total reports for this product
        n_product = await _get_total_product_reports(product_names)
        total_product_reports += n_product

        if n_product == 0:
            logger.info("No FAERS reports for %s; skipping", brand)
            continue

        for ae in TARGET_AES:
            # Cell a: drug AND event
            a = await _get_drug_ae_count(product_names, ae)
            if a == 0:
                continue

            # Cell b: drug, NOT event
            b = max(n_product - a, 0)

            # Cell c: NOT drug, WITH event
            n_ae_total = await _get_total_ae_reports(ae)
            c = max(n_ae_total - a, 0)

            # Cell d: NOT drug, NOT event
            d = max(n_total_database - a - b - c, 0)

            # Compute disproportionality metrics
            prr, prr_ci_low, prr_ci_high = compute_prr(a, b, c, d)
            ror, ror_ci_low, ror_ci_high = compute_ror(a, b, c, d)

            # Expected count for EBGM
            N = a + b + c + d
            expected = ((a + b) * (a + c)) / N if N > 0 else 0.0
            ebgm, ebgm05 = compute_ebgm(a, expected)

            # Classify
            is_signal, signal_strength = classify_signal(
                prr, prr_ci_low, ror, ror_ci_low, ebgm05, a,
            )

            signals.append(
                FAERSSignal(
                    product=brand,
                    adverse_event=ae,
                    n_cases=a,
                    n_total_product=n_product,
                    n_total_ae=n_ae_total,
                    n_total_database=n_total_database,
                    prr=round(prr, 4),
                    prr_ci_low=round(prr_ci_low, 4),
                    prr_ci_high=round(prr_ci_high, 4),
                    ror=round(ror, 4),
                    ror_ci_low=round(ror_ci_low, 4),
                    ror_ci_high=round(ror_ci_high, 4),
                    ebgm=round(ebgm, 4),
                    ebgm05=round(ebgm05, 4),
                    is_signal=is_signal,
                    signal_strength=signal_strength,
                )
            )

            logger.debug(
                "Signal: %s + %s | a=%d PRR=%.2f [%.2f-%.2f] "
                "ROR=%.2f [%.2f-%.2f] EBGM=%.2f EBGM05=%.2f => %s",
                brand, ae, a, prr, prr_ci_low, prr_ci_high,
                ror, ror_ci_low, ror_ci_high, ebgm, ebgm05,
                signal_strength,
            )

    # Sort: detected signals first, then by PRR descending
    signals.sort(key=lambda s: (not s.is_signal, -s.prr))

    signals_detected = sum(1 for s in signals if s.is_signal)
    strong_signals = sum(1 for s in signals if s.signal_strength == "strong")

    return FAERSSummary(
        products_queried=products_to_query,
        total_reports=total_product_reports,
        signals_detected=signals_detected,
        strong_signals=strong_signals,
        signals=signals,
        query_timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def get_faers_summary() -> dict:
    """High-level summary of FAERS data for all CAR-T products.

    Returns a dict with product-level report counts and top signals, suitable
    for quick dashboard display.

    Returns:
        Dict with keys:
            - ``products``: List of dicts with brand_name, total_reports,
              and top_adverse_events for each product.
            - ``total_reports``: Sum across all products.
            - ``query_timestamp``: ISO-8601 timestamp.
            - ``data_source``: Attribution string.
    """
    product_summaries: list[dict] = []
    total_all = 0

    for brand, names in CAR_T_PRODUCTS.items():
        total_reports = await _get_total_product_reports(names)
        total_all += total_reports

        top_aes: list[dict] = []
        if total_reports > 0:
            # Get top adverse events for this product
            for name in names:
                params = {
                    "search": f'patient.drug.openfda.brand_name:"{name}"',
                    "count": "patient.reaction.reactionmeddrapt.exact",
                    "limit": "10",
                }
                data = await _http_get_json(OPENFDA_BASE, params)
                if data and "results" in data:
                    for r in data["results"][:10]:
                        top_aes.append({
                            "term": r.get("term", ""),
                            "count": r.get("count", 0),
                        })
                    break  # Got results from this name variant

        product_summaries.append({
            "brand_name": brand,
            "generic_name": names[-1] if len(names) > 1 else names[0],
            "total_reports": total_reports,
            "top_adverse_events": top_aes,
        })

    # Sort by total reports descending
    product_summaries.sort(key=lambda p: -p["total_reports"])

    return {
        "products": product_summaries,
        "total_reports": total_all,
        "query_timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": "FDA Adverse Event Reporting System (FAERS) via openFDA",
    }
