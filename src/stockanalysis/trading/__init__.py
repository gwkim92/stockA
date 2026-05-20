"""Trading safety and paper validation helpers.

This package intentionally does not contain a broker client or order submission
adapter. It only evaluates and records order intent decisions.
"""

from stockanalysis.trading.paper_safety_bootstrap import run_paper_safety_bootstrap_config
from stockanalysis.trading.paper_validation import run_paper_validation_audit

__all__ = ["run_paper_safety_bootstrap_config", "run_paper_validation_audit"]
