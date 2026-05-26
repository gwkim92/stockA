#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_project_execution_roadmap.sh
python3 -m compileall src tests >/dev/null

test -f docs/project-execution-roadmap.md
test -f docs/tasks/project-execution-roadmap/contract.md
test -f docs/tasks/project-execution-roadmap/plan.md
test -f docs/tasks/project-execution-roadmap/handoff.md
test -f docs/tasks/project-execution-roadmap/review.md

grep -q "Current State" docs/project-execution-roadmap.md
grep -q "Not Done" docs/project-execution-roadmap.md
grep -q "Execution Order" docs/project-execution-roadmap.md
grep -q "Live Read Completeness" docs/project-execution-roadmap.md
grep -q "API Runtime Boundary" docs/project-execution-roadmap.md
grep -q "Data Operations Loop" docs/project-execution-roadmap.md
grep -q "AI Runtime" docs/project-execution-roadmap.md
grep -q "Recommendation And Cycle Quality" docs/project-execution-roadmap.md
grep -q "Frontend Productization" docs/project-execution-roadmap.md
grep -q "frontend-runtime-db-smoke" docs/project-execution-roadmap.md
grep -q "frontend-api-server-framework-decision" docs/project-execution-roadmap.md
grep -q "frontend-api-server-observability-hardening" docs/project-execution-roadmap.md
grep -q "frontend-api-server-deployment-boundary" docs/project-execution-roadmap.md
grep -q "frontend-api-pagination-conventions" docs/project-execution-roadmap.md
grep -q "frontend-api-observability-sink-decision" docs/project-execution-roadmap.md
grep -q "frontend-api-otel-exporter-pilot" docs/project-execution-roadmap.md
grep -q "frontend-api-sql-pagination-optimization" docs/project-execution-roadmap.md
grep -q "frontend-api-local-collector-smoke" docs/project-execution-roadmap.md
grep -q "frontend-api-alert-rules" docs/project-execution-roadmap.md
grep -q "secret-free alert rule reference" docs/project-execution-roadmap.md
grep -q "data-operations-cadence-foundation" docs/project-execution-roadmap.md
grep -q "data-operations-artifact-runner" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-env-readiness" docs/project-execution-roadmap.md
grep -q "data-operations-runtime-smoke" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-install-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-alert-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-runbook" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-operator-dry-run" docs/project-execution-roadmap.md
grep -q "data-operations-scheduler-activation-approval-gate" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-user-decision" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-activation-final-preflight" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-host-activation-plan" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-host-activation-execution-request" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-host-activation-execution-decision" docs/project-execution-roadmap.md
grep -q "data-operations-backend-orchestration-boundary" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-host-activation-execution-final-preflight" docs/project-execution-roadmap.md
grep -q "data-operations-live-scheduler-host-activation-execution" docs/project-execution-roadmap.md
grep -q "manual-host-scheduler-activation-explicit-approval" docs/project-execution-roadmap.md
grep -q "manual-host-scheduler-activation-preflight" docs/project-execution-roadmap.md
grep -q "local-live-mvp-runtime" docs/project-execution-roadmap.md
grep -q "stockanalysis-operations" docs/project-execution-roadmap.md
test -f docs/tasks/data-operations-backend-orchestration-boundary/contract.md
test -f docs/tasks/data-operations-backend-orchestration-boundary/plan.md
test -f docs/tasks/data-operations-backend-orchestration-boundary/handoff.md
test -f docs/tasks/data-operations-backend-orchestration-boundary/review.md
test -f docs/data-operations-backend-orchestration-boundary.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/review.md
test -f docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/contract.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/plan.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/handoff.md
test -f docs/tasks/data-operations-live-scheduler-host-activation-execution/review.md
test -f docs/data-operations-live-scheduler-host-activation-execution.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/contract.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/plan.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/handoff.md
test -f docs/tasks/manual-host-scheduler-activation-explicit-approval/review.md
test -f docs/manual-host-scheduler-activation-explicit-approval.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/contract.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/plan.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/handoff.md
test -f docs/tasks/manual-host-scheduler-activation-preflight/review.md
test -f docs/manual-host-scheduler-activation-preflight.md
test -f docs/tasks/local-live-mvp-runtime/contract.md
test -f docs/tasks/local-live-mvp-runtime/plan.md
test -f docs/tasks/local-live-mvp-runtime/handoff.md
test -f docs/tasks/local-live-mvp-runtime/review.md
test -f docs/local-live-mvp-runtime.md
test -f docs/tasks/local-first-runtime-direction/contract.md
test -f docs/tasks/local-first-runtime-direction/handoff.md
test -f docs/tasks/local-first-runtime-direction/review.md
test -f docs/plans/2026-05-20-local-first-runtime-direction.md
test -f docs/local-first-runtime-direction.md
test -f docs/tasks/local-runtime-status-orchestrator/contract.md
test -f docs/tasks/local-runtime-status-orchestrator/handoff.md
test -f docs/tasks/local-runtime-status-orchestrator/review.md
test -f docs/plans/2026-05-20-local-runtime-status-orchestrator.md
test -f docs/local-runtime-status-orchestrator.md
test -f docs/tasks/manual-local-ingest-smoke/contract.md
test -f docs/tasks/manual-local-ingest-smoke/handoff.md
test -f docs/tasks/manual-local-ingest-smoke/review.md
test -f docs/plans/2026-05-20-manual-local-ingest-smoke.md
test -f docs/manual-local-ingest-smoke.md
test -f docs/tasks/manual-local-ingest-data-health-visibility/contract.md
test -f docs/tasks/manual-local-ingest-data-health-visibility/handoff.md
test -f docs/tasks/manual-local-ingest-data-health-visibility/review.md
test -f docs/plans/2026-05-20-manual-local-ingest-data-health-visibility.md
test -f docs/manual-local-ingest-data-health-visibility.md
test -f scripts/verify_manual_local_ingest_data_health_visibility.sh
test -f docs/tasks/local-ai-pipeline-run-alignment/contract.md
test -f docs/tasks/local-ai-pipeline-run-alignment/handoff.md
test -f docs/tasks/local-ai-pipeline-run-alignment/review.md
test -f docs/plans/2026-05-20-local-ai-pipeline-run-alignment.md
test -f docs/local-ai-pipeline-run-alignment.md
test -f scripts/verify_local_ai_pipeline_run_alignment.sh
test -f docs/tasks/local-ingest-worker-loop/contract.md
test -f docs/tasks/local-ingest-worker-loop/handoff.md
test -f docs/tasks/local-ingest-worker-loop/review.md
test -f docs/plans/2026-05-20-local-ingest-worker-loop.md
test -f docs/local-ingest-worker-loop.md
test -f scripts/verify_local_ingest_worker_loop.sh
test -f docs/tasks/local-ingest-worker-data-health-visibility/contract.md
test -f docs/tasks/local-ingest-worker-data-health-visibility/handoff.md
test -f docs/tasks/local-ingest-worker-data-health-visibility/review.md
test -f docs/plans/2026-05-20-local-ingest-worker-data-health-visibility.md
test -f docs/local-ingest-worker-data-health-visibility.md
test -f scripts/verify_local_ingest_worker_data_health_visibility.sh
test -f docs/tasks/server-scheduler-invocation-boundary/contract.md
test -f docs/tasks/server-scheduler-invocation-boundary/plan.md
test -f docs/tasks/server-scheduler-invocation-boundary/handoff.md
test -f docs/tasks/server-scheduler-invocation-boundary/review.md
test -f docs/plans/2026-05-20-server-scheduler-invocation-boundary.md
test -f docs/server-scheduler-invocation-boundary.md
test -f scripts/verify_server_scheduler_invocation_boundary.sh
test -f docs/tasks/server-scheduler-deployment-target-decision/contract.md
test -f docs/tasks/server-scheduler-deployment-target-decision/plan.md
test -f docs/tasks/server-scheduler-deployment-target-decision/handoff.md
test -f docs/tasks/server-scheduler-deployment-target-decision/review.md
test -f docs/plans/2026-05-20-server-scheduler-deployment-target-decision.md
test -f docs/server-scheduler-deployment-target-decision.md
test -f scripts/verify_server_scheduler_deployment_target_decision.sh
test -f docs/tasks/hosted-database-runtime-decision/contract.md
test -f docs/tasks/hosted-database-runtime-decision/plan.md
test -f docs/tasks/hosted-database-runtime-decision/handoff.md
test -f docs/tasks/hosted-database-runtime-decision/review.md
test -f docs/plans/2026-05-20-hosted-database-runtime-decision.md
test -f docs/hosted-database-runtime-decision.md
test -f scripts/verify_hosted_database_runtime_decision.sh
grep -q 'Current task group: `professional-equity-analysis-foundation`' docs/project-execution-roadmap.md
grep -q '현재 고정된 immediate next task는 `recommendation-outcome-calibration-sample-expansion-v1`' AGENTS.md
test -f docs/tasks/portfolio-risk-budget-drift-quality-audit/contract.md
test -f docs/tasks/portfolio-risk-budget-drift-quality-audit/handoff.md
test -f docs/tasks/portfolio-risk-budget-rebalance-candidate-review/contract.md
test -f docs/tasks/portfolio-risk-budget-rebalance-candidate-review/handoff.md
test -f docs/tasks/portfolio-position-sizing-policy-v1/contract.md
test -f docs/tasks/portfolio-position-sizing-policy-v1/handoff.md
test -f docs/tasks/recommendation-professional-decision-waterfall-v1/contract.md
test -f docs/tasks/recommendation-professional-decision-waterfall-v1/handoff.md
test -f docs/tasks/thesis-lifecycle-professional-gates-v1/contract.md
test -f docs/tasks/thesis-lifecycle-professional-gates-v1/handoff.md
test -f docs/tasks/thesis-lifecycle-professional-gates-v1/review.md
test -f docs/tasks/valuation-target-range-foundation-v1/contract.md
test -f docs/tasks/valuation-target-range-foundation-v1/handoff.md
test -f docs/tasks/financial-statement-model-detail-v1/contract.md
test -f docs/tasks/financial-statement-model-detail-v1/handoff.md
test -f docs/tasks/financial-statement-model-detail-v1/review.md
grep -q "professional-coverage-expansion-for-active-recommendations" docs/project-execution-roadmap.md
grep -q "recommendation-weight-review-readiness-audit" docs/project-execution-roadmap.md
grep -q "paper-validation-conflict-remediation" docs/project-execution-roadmap.md
grep -q "portfolio-holding-coverage-remediation" docs/project-execution-roadmap.md
grep -q "paper-safety-interlock-policy" docs/project-execution-roadmap.md
grep -q "manual-weight-review-calibration-report" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-policy-v2" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-guardrail-run" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-paper-validation-integration" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-frontend-guardrail-visibility" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-benchmark-composition-v1" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-benchmark-provider-import-v1" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-drift-quality-audit" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-full-holdings-source" docs/project-execution-roadmap.md
grep -q "portfolio-risk-budget-rebalance-candidate-review" docs/project-execution-roadmap.md
grep -q "portfolio-position-sizing-policy-v1" docs/project-execution-roadmap.md
grep -q "recommendation-professional-decision-waterfall-v1" docs/project-execution-roadmap.md
grep -q "thesis-lifecycle-professional-gates-v1" docs/project-execution-roadmap.md
grep -q "valuation-target-range-foundation-v1" docs/project-execution-roadmap.md
grep -q "financial-statement-model-detail-v1" docs/project-execution-roadmap.md
grep -q "recommendation-financial-model-waterfall-integration-v1" docs/project-execution-roadmap.md
grep -q "valuation-model-quality-depth-v1" docs/project-execution-roadmap.md
grep -q "financial-forecast-and-scenario-inputs-v1" docs/project-execution-roadmap.md
grep -q "sum-of-the-parts-valuation-foundation-v1" docs/project-execution-roadmap.md
grep -q "segment-footnote-extraction-foundation-v1" docs/project-execution-roadmap.md
grep -q "reported-segment-footnote-parser-v1" docs/project-execution-roadmap.md
grep -q "financial-period-source-document-linkage-v1" docs/project-execution-roadmap.md
grep -q "reported-segment-parser-quality-v1" docs/project-execution-roadmap.md
grep -q "segment-level-sotp-inputs-v1" docs/project-execution-roadmap.md
grep -q "segment-level-sotp-valuation-allocation-v1" docs/project-execution-roadmap.md
grep -q "reported-segment-unit-normalization-v1" docs/project-execution-roadmap.md
grep -q "segment-specific-sotp-assumptions-v1" docs/project-execution-roadmap.md
grep -q "segment-sotp-driver-calibration-v1" docs/project-execution-roadmap.md
grep -q "segment-history-backfill-v1" docs/project-execution-roadmap.md
grep -q "segment-history-coverage-expansion-v1" docs/project-execution-roadmap.md
grep -q "reported-segment-parser-layout-expansion-v1" docs/project-execution-roadmap.md
grep -q "segment-history-coverage-breadth-expansion-v1" docs/project-execution-roadmap.md
grep -q "aeis-reported-segment-parser-layout-v1" docs/project-execution-roadmap.md
grep -q "segment-history-source-linkage-remediation-v1" docs/project-execution-roadmap.md
grep -q "professional-coverage-refresh-after-source-remediation-v1" docs/project-execution-roadmap.md
grep -q "portfolio-and-fund-instrument-analysis-v1" docs/project-execution-roadmap.md
grep -q "fund-expense-tracking-source-v1" docs/project-execution-roadmap.md
grep -q "fund-expense-ratio-public-source-v1" docs/project-execution-roadmap.md
grep -q "fund-nav-premium-discount-source-v1" docs/project-execution-roadmap.md
grep -q "fund-tracking-error-source-v1" docs/project-execution-roadmap.md
grep -q "recommendation-outcome-calibration-sample-expansion-v1" docs/project-execution-roadmap.md
test -f docs/tasks/fund-tracking-error-source-v1/contract.md
test -f docs/tasks/fund-tracking-error-source-v1/handoff.md
test -f docs/tasks/fund-tracking-error-source-v1/review.md
test -f docs/plans/2026-05-27-fund-tracking-error-source-v1.md
test -f docs/tasks/recommendation-outcome-calibration-sample-expansion-v1/contract.md
test -f docs/tasks/recommendation-outcome-calibration-sample-expansion-v1/handoff.md
test -f docs/tasks/recommendation-outcome-calibration-sample-expansion-v1/review.md
test -f docs/plans/2026-05-27-recommendation-outcome-calibration-sample-expansion-v1.md
grep -q "segment-history-coverage-expansion-run" src/stockanalysis/operations/cli.py
test -f src/stockanalysis/operations/segment_history_coverage_expansion.py
test -f tests/test_segment_history_coverage_expansion.py
test -f docs/tasks/financial-period-source-document-linkage-v1/contract.md
test -f docs/tasks/financial-period-source-document-linkage-v1/handoff.md
test -f docs/tasks/financial-period-source-document-linkage-v1/review.md
test -f docs/plans/2026-05-26-financial-period-source-document-linkage-v1.md
test -f docs/tasks/reported-segment-parser-quality-v1/contract.md
test -f docs/tasks/reported-segment-parser-quality-v1/handoff.md
test -f docs/tasks/reported-segment-parser-quality-v1/review.md
test -f docs/plans/2026-05-26-reported-segment-parser-quality-v1.md
test -f docs/tasks/segment-level-sotp-inputs-v1/contract.md
test -f docs/tasks/segment-level-sotp-inputs-v1/handoff.md
test -f docs/tasks/segment-level-sotp-inputs-v1/review.md
test -f docs/plans/2026-05-26-segment-level-sotp-inputs-v1.md
test -f docs/tasks/segment-level-sotp-valuation-allocation-v1/contract.md
test -f docs/tasks/segment-level-sotp-valuation-allocation-v1/handoff.md
test -f docs/tasks/segment-level-sotp-valuation-allocation-v1/review.md
test -f docs/plans/2026-05-26-segment-level-sotp-valuation-allocation-v1.md
test -f docs/tasks/reported-segment-unit-normalization-v1/contract.md
test -f docs/tasks/reported-segment-unit-normalization-v1/handoff.md
test -f docs/tasks/reported-segment-unit-normalization-v1/review.md
test -f docs/plans/2026-05-26-reported-segment-unit-normalization-v1.md
test -f docs/tasks/segment-specific-sotp-assumptions-v1/contract.md
test -f docs/tasks/segment-specific-sotp-assumptions-v1/handoff.md
test -f docs/tasks/segment-specific-sotp-assumptions-v1/review.md
test -f docs/plans/2026-05-26-segment-specific-sotp-assumptions-v1.md
test -f docs/tasks/segment-sotp-driver-calibration-v1/contract.md
test -f docs/tasks/segment-sotp-driver-calibration-v1/handoff.md
test -f docs/tasks/segment-sotp-driver-calibration-v1/review.md
test -f docs/plans/2026-05-26-segment-sotp-driver-calibration-v1.md
test -f docs/tasks/segment-history-backfill-v1/contract.md
test -f docs/tasks/segment-history-backfill-v1/handoff.md
test -f docs/tasks/segment-history-backfill-v1/review.md
test -f docs/plans/2026-05-26-segment-history-backfill-v1.md
test -f docs/tasks/segment-history-coverage-expansion-v1/contract.md
test -f docs/tasks/segment-history-coverage-expansion-v1/handoff.md
test -f docs/tasks/segment-history-coverage-expansion-v1/review.md
test -f docs/plans/2026-05-26-segment-history-coverage-expansion-v1.md
test -f docs/tasks/reported-segment-parser-layout-expansion-v1/contract.md
test -f docs/tasks/reported-segment-parser-layout-expansion-v1/handoff.md
test -f docs/tasks/reported-segment-parser-layout-expansion-v1/review.md
test -f docs/plans/2026-05-26-reported-segment-parser-layout-expansion-v1.md
test -f docs/tasks/segment-history-coverage-breadth-expansion-v1/contract.md
test -f docs/tasks/segment-history-coverage-breadth-expansion-v1/handoff.md
test -f docs/tasks/segment-history-coverage-breadth-expansion-v1/review.md
test -f docs/plans/2026-05-26-segment-history-coverage-breadth-expansion-v1.md
test -f docs/tasks/aeis-reported-segment-parser-layout-v1/contract.md
test -f docs/tasks/aeis-reported-segment-parser-layout-v1/handoff.md
test -f docs/tasks/aeis-reported-segment-parser-layout-v1/review.md
test -f docs/plans/2026-05-26-aeis-reported-segment-parser-layout-v1.md
test -f docs/tasks/segment-history-source-linkage-remediation-v1/contract.md
test -f docs/tasks/segment-history-source-linkage-remediation-v1/handoff.md
test -f docs/tasks/segment-history-source-linkage-remediation-v1/review.md
test -f docs/plans/2026-05-26-segment-history-source-linkage-remediation-v1.md
test -f docs/tasks/professional-coverage-refresh-after-source-remediation-v1/contract.md
test -f docs/tasks/professional-coverage-refresh-after-source-remediation-v1/handoff.md
test -f docs/tasks/professional-coverage-refresh-after-source-remediation-v1/review.md
test -f docs/plans/2026-05-26-professional-coverage-refresh-after-source-remediation-v1.md
test -f docs/tasks/portfolio-and-fund-instrument-analysis-v1/contract.md
test -f docs/tasks/portfolio-and-fund-instrument-analysis-v1/handoff.md
test -f docs/tasks/portfolio-and-fund-instrument-analysis-v1/review.md
test -f docs/plans/2026-05-26-portfolio-and-fund-instrument-analysis-v1.md
test -f docs/tasks/fund-expense-tracking-source-v1/contract.md
test -f docs/tasks/fund-expense-tracking-source-v1/handoff.md
test -f docs/tasks/fund-expense-tracking-source-v1/review.md
test -f docs/plans/2026-05-26-fund-expense-tracking-source-v1.md
test -f docs/tasks/fund-expense-ratio-public-source-v1/contract.md
test -f docs/tasks/fund-expense-ratio-public-source-v1/handoff.md
test -f docs/tasks/fund-expense-ratio-public-source-v1/review.md
test -f docs/plans/2026-05-26-fund-expense-ratio-public-source-v1.md
test -f docs/tasks/fund-nav-premium-discount-source-v1/contract.md
test -f docs/tasks/fund-nav-premium-discount-source-v1/handoff.md
test -f docs/tasks/fund-nav-premium-discount-source-v1/review.md
test -f docs/plans/2026-05-27-fund-nav-premium-discount-source-v1.md
test -f docs/tasks/fund-tracking-error-source-v1/contract.md
test -f docs/tasks/fund-tracking-error-source-v1/handoff.md
test -f docs/tasks/fund-tracking-error-source-v1/review.md
test -f docs/plans/2026-05-27-fund-tracking-error-source-v1.md
test -f docs/tasks/financial-forecast-and-scenario-inputs-v1/contract.md
test -f docs/tasks/financial-forecast-and-scenario-inputs-v1/handoff.md
test -f docs/tasks/financial-forecast-and-scenario-inputs-v1/review.md
test -f docs/tasks/sum-of-the-parts-valuation-foundation-v1/contract.md
test -f docs/tasks/sum-of-the-parts-valuation-foundation-v1/handoff.md
test -f docs/tasks/sum-of-the-parts-valuation-foundation-v1/review.md
test -f docs/plans/2026-05-26-sum-of-the-parts-valuation-foundation-v1.md
test -f docs/tasks/segment-footnote-extraction-foundation-v1/contract.md
test -f docs/tasks/segment-footnote-extraction-foundation-v1/handoff.md
test -f docs/tasks/segment-footnote-extraction-foundation-v1/review.md
test -f docs/plans/2026-05-26-segment-footnote-extraction-foundation-v1.md
test -f docs/tasks/reported-segment-footnote-parser-v1/contract.md
test -f docs/tasks/reported-segment-footnote-parser-v1/handoff.md
test -f docs/tasks/reported-segment-footnote-parser-v1/review.md
test -f docs/plans/2026-05-26-reported-segment-footnote-parser-v1.md
grep -q "project-roadmap-reality-sync" docs/project-execution-roadmap.md
grep -q "cycle-ai-e2e-quality-audit" docs/project-execution-roadmap.md
grep -q "news-ai-eval-dataset-and-scoring" docs/project-execution-roadmap.md
grep -q "cycle-community-ai-summary-v2" docs/project-execution-roadmap.md
grep -q "recommendation-quality-calibration" docs/project-execution-roadmap.md
grep -q "local-first runtime" docs/project-execution-roadmap.md
grep -q "local-runtime-status-orchestrator" docs/project-execution-roadmap.md
grep -q "manual-local-ingest-smoke" docs/project-execution-roadmap.md
grep -q "manual-local-ingest-data-health-visibility" docs/project-execution-roadmap.md
grep -q "local-ai-pipeline-run-alignment" docs/project-execution-roadmap.md
grep -q "local-ingest-worker-loop" docs/project-execution-roadmap.md
grep -q "local-ingest-worker-data-health-visibility" docs/project-execution-roadmap.md
grep -q "server-scheduler-invocation-boundary" docs/project-execution-roadmap.md
grep -q "server-scheduler-deployment-target-decision" docs/project-execution-roadmap.md
grep -q "hosted-database-runtime-decision" docs/project-execution-roadmap.md
grep -q "stockanalysis-operations" AGENTS.md
grep -q "docs/project-execution-roadmap.md" README.md
grep -q "verify_project_execution_roadmap.sh" docs/verification-plan.md
grep -q "tests.test_data_operations_cli" docs/verification-plan.md
grep -q "verify_local_ai_pipeline_run_alignment.sh" docs/verification-plan.md
grep -q "verify_local_ingest_worker_loop.sh" docs/verification-plan.md
grep -q "verify_local_ingest_worker_data_health_visibility.sh" docs/verification-plan.md
grep -q "verify_server_scheduler_invocation_boundary.sh" docs/verification-plan.md
grep -q "verify_server_scheduler_deployment_target_decision.sh" docs/verification-plan.md
grep -q "verify_hosted_database_runtime_decision.sh" docs/verification-plan.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh" docs/verification-plan.md
grep -q "verify_data_operations_live_scheduler_host_activation_execution.sh" docs/verification-plan.md
grep -q "verify_manual_host_scheduler_activation_explicit_approval.sh" docs/verification-plan.md
grep -q "verify_manual_host_scheduler_activation_preflight.sh" docs/verification-plan.md

if grep -q "실거래 자동화는 별도 승인 전까지 범위 밖이다" AGENTS.md; then
  true
else
  echo "AGENTS.md must keep real-trading automation out of scope." >&2
  exit 1
fi

echo "project execution roadmap verification passed"
