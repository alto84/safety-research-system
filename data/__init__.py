"""
Synthetic patient cohort data for CAR-T cell therapy safety prediction.

Generates realistic patient cohorts matching 6 published landmark CAR-T trials:
  ZUMA-1, JULIET, ELARA, KarMMa, CARTITUDE-1, TRANSCEND

Usage:
    from data.synthetic_cohorts import generate_all_cohorts
    cohorts, mega_cohort = generate_all_cohorts()

    from data.edge_cases import generate_edge_cases
    edge = generate_edge_cases()
"""

from data.synthetic_cohorts import generate_all_cohorts
from data.edge_cases import generate_edge_cases

__all__ = ["generate_all_cohorts", "generate_edge_cases"]
