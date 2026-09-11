"""Select comparable statement facts without mixing duration or filing vintages.

Companyfacts fy/fp describe the filing, not necessarily a comparative fact.
Calendar frames cannot identify the issuer's fiscal year. Anchor on the latest
statement duration in the same accession, then match anniversaries (52/53 weeks).
No cross-filing subtraction or inferred quarterly cash flow is performed.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from stockanalysis.ingest.sec.models import SecCompanyFactsSyncResult, SecCompanyFactsValueRecord

PERIOD_POLICY = "sec-statement-duration-v2"
FORMS = {"10-K": "annual", "20-F": "annual", "10-Q": "quarterly"}
FLOW_ANCHORS = {"revenue", "gross_profit", "net_income", "operating_income", "operating_cash_flow"}


def select_statement_facts(payload: dict, *, concepts: dict, instant_metrics: set,
                           units: dict) -> SecCompanyFactsSyncResult:
    candidates = []
    anchors: dict[str, date] = {}
    excluded = {}
    skipped = 0

    def reject(evidence, reason):
        # Preserve the latest observed exclusion for each distinct duration/tag.
        # Selected facts retain their exact filing separately in the run ledger.
        key = (evidence.get("namespace"), evidence.get("concept"), evidence.get("unit"),
               evidence.get("start"), evidence.get("end"), reason)
        value = {**evidence, "exclusion_reason": reason}
        if key not in excluded or str(value.get("filed", "")) >= str(excluded[key].get("filed", "")):
            excluded[key] = value

    for namespace in ("us-gaap", "dei"):
        namespace_facts = payload.get("facts", {}).get(namespace, {})
        if not isinstance(namespace_facts, dict):
            continue
        for concept, body in namespace_facts.items():
            metric = concepts.get(concept)
            if not isinstance(body, dict) or not isinstance(body.get("units"), dict):
                skipped += int(metric is not None)
                continue
            for unit, items in body["units"].items():
                if not isinstance(items, list):
                    continue
                for raw in items:
                    if not isinstance(raw, dict):
                        skipped += 1
                        continue
                    evidence = {**raw, "namespace": namespace, "concept": concept, "unit": unit}
                    form = str(raw.get("form", "")).removesuffix("/A")
                    scope = FORMS.get(form)
                    if scope is None:
                        if metric:
                            skipped += 1
                            reject(evidence, "unsupported_form")
                        continue
                    try:
                        end = date.fromisoformat(raw["end"])
                        start = date.fromisoformat(raw["start"]) if raw.get("start") else None
                        filed = date.fromisoformat(raw["filed"])
                        fy = int(raw["fy"])
                        accn = str(raw["accn"])
                        value = Decimal(str(raw["val"]))
                        if not accn or not value.is_finite() or filed < end:
                            raise ValueError("Invalid filing fact")
                    except (KeyError, TypeError, ValueError, InvalidOperation):
                        if metric:
                            skipped += 1
                            reject(evidence, "invalid_or_missing_filing_metadata")
                        continue
                    days = (end - start).days + 1 if start else 0
                    duration_ok = 335 <= days <= 395 if scope == "annual" else 75 <= days <= 110
                    # Use all US GAAP duration concepts to find the current
                    # statement end, including concepts we do not import.
                    if namespace == "us-gaap" and duration_ok:
                        anchors[accn] = max(anchors.get(accn, end), end)
                    if metric is None:
                        continue
                    if unit != units.get(metric, "USD"):
                        skipped += 1
                        reject(evidence, "unsupported_unit")
                        continue
                    instant = start is None and metric in instant_metrics
                    if not instant and (metric in instant_metrics or not duration_ok):
                        skipped += 1
                        reject(evidence, "non_statement_duration_or_duration_shares")
                        continue
                    quarter = None
                    if scope == "quarterly":
                        fp = str(raw.get("fp", ""))
                        if fp not in {"Q1", "Q2", "Q3", "Q4"}:
                            skipped += 1
                            reject(evidence, "unknown_fiscal_quarter")
                            continue
                        quarter = int(fp[1])
                    candidates.append(dict(scope=scope, start=start, end=end, filed=filed,
                                           fy=fy, quarter=quarter, accn=accn, value=value,
                                           metric=metric, unit=unit, evidence=evidence))

    groups = defaultdict(list)
    for item in candidates:
        anchor = anchors.get(item["accn"])
        delta = (anchor - item["end"]).days if anchor else -1
        years = round(delta / 365.25)
        # A prior quarter or fiscal-calendar change is not a prior-year
        # comparable simply because the filing supplied fy/fp.
        if delta < 0 or abs(delta - years * 365.25) > 14:
            skipped += 1
            reject(item["evidence"], "unresolved_fiscal_period")
            continue
        item["actual_fy"] = item["fy"] - years
        item["anchor"] = anchor
        groups[(item["scope"], item["end"], item["accn"])].append(item)

    statements = defaultdict(list)
    for (scope, end, accn), items in groups.items():
        starts = {i["start"] for i in items if i["metric"] in FLOW_ANCHORS and i["start"] is not None}
        identities = {(i["actual_fy"], i["quarter"]) for i in items}
        if len(starts) != 1 or len(identities) != 1:
            for item in items:
                skipped += 1
                reject(item["evidence"], "missing_or_ambiguous_statement_anchor")
            continue
        start = next(iter(starts))
        compatible = []
        for item in items:
            if item["start"] is not None and item["start"] != start:
                skipped += 1
                reject(item["evidence"], "incompatible_statement_start")
            else:
                compatible.append(item)
        statements[(scope, end)].append((max(i["filed"] for i in compatible), accn, start, compatible))

    records = []
    # Explicit concept order is stable when the provider changes JSON ordering.
    priority = {concept: len(concepts) - index for index, concept in enumerate(concepts)}
    for (scope, end), versions in sorted(statements.items()):
        filed, accn, start, items = max(versions, key=lambda v: (v[0], v[1]))
        metrics = {}
        for item in items:
            existing = metrics.get(item["metric"])
            if existing is None or priority[item["evidence"]["concept"]] > priority[existing["evidence"]["concept"]]:
                metrics[item["metric"]] = item
        for metric, item in sorted(metrics.items()):
            if len({i["value"] for i in items if i["evidence"]["concept"] == item["evidence"]["concept"]}) > 1:
                skipped += 1
                reject(item["evidence"], "conflicting_values_in_same_filing")
                continue
            records.append(SecCompanyFactsValueRecord(
                accession_number=accn, statement_scope=scope, fiscal_year=item["actual_fy"],
                fiscal_quarter=item["quarter"], period_start=start, period_end=end,
                report_date=filed, currency_code="USD", is_audited=scope == "annual",
                metric_code=metric, metric_value=item["value"], unit=item["unit"],
                source_evidence={**item["evidence"], "fiscal_period_anchor_end": item["anchor"].isoformat(),
                                 "fiscal_year_basis": "same_accession_statement_anniversary",
                                 "selected_statement_start": start.isoformat(), "actual_fiscal_year": item["actual_fy"]},
            ))
    return SecCompanyFactsSyncResult(
        cik=str(payload["cik"]).zfill(10), company_name=str(payload["entityName"]),
        values=tuple(sorted(records, key=lambda r: (r.period_end, r.statement_scope, r.metric_code))),
        skipped_count=skipped, period_policy=PERIOD_POLICY,
        excluded_facts=tuple(excluded.values()),
    )
