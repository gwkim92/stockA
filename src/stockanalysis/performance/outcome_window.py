"""Shared SQL identity for the existing calendar-horizon outcome audit.

The seven-day tolerance is the established audit policy, not a new return or
benchmark definition. Fragments passed here are internal SQL expressions.
"""


def outcome_window_match_sql(*, recommendation_id: str, recommendation_date: str,
                             horizon_days: str, end_date: str, alias: str = "outcome") -> str:
    return f"""{alias}.recommendation_id = {recommendation_id}
          and {alias}.measurement_end_date <= {end_date}
          and {alias}.measurement_end_date >= {recommendation_date}
          and {alias}.horizon_days between greatest({horizon_days} - 7, 0) and {horizon_days} + 7"""
