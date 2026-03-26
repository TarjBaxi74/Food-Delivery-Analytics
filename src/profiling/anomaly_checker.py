"""
QA Profiling — Anomaly Checker
================================
Runs after the Silver layer to surface data quality issues before
any mart-level aggregation. Each check returns a structured finding
so the pipeline can log, alert, or halt depending on severity.

Checks implemented:
  1. Null rates per column (warns if > threshold)
  2. Duplicate key detection
  3. Orphan events (delivery events with no matching order)
  4. Order value outliers (> 3 std devs from mean)
  5. Refund rate spike (per-city refund rate vs overall average)
  6. SLA breach rate by city (flags cities above 2x the fleet average)
  7. Rider assignment gaps (delivered events with no rider_id)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import numpy as np


# ── Severity levels ──────────────────────────────────────────────────────────

WARN = "WARN"
FAIL = "FAIL"
OK   = "OK"


@dataclass
class AnomalyFinding:
    check: str
    severity: str          # OK | WARN | FAIL
    detail: str
    value: Any = None      # the actual metric that triggered the finding


@dataclass
class ProfileReport:
    table: str
    findings: list[AnomalyFinding] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return any(f.severity == FAIL for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity == WARN for f in self.findings)

    def print(self):
        status_icon = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}
        print(f"\n  Profile: {self.table}")
        for f in self.findings:
            icon = status_icon.get(f.severity, "?")
            print(f"    [{icon}] {f.check}: {f.detail}")


# ── Thresholds (tunable) ──────────────────────────────────────────────────────

NULL_RATE_WARN  = 0.05   # 5%  null rate triggers WARN
NULL_RATE_FAIL  = 0.20   # 20% null rate triggers FAIL
ORPHAN_RATE_FAIL = 0.05  # 5%  orphan rate triggers FAIL
OUTLIER_ZSCORE  = 3.0    # z-score threshold for order_value outliers
REFUND_RATE_MULTIPLIER = 2.0   # city refund rate > 2x fleet avg → WARN
SLA_BREACH_MULTIPLIER  = 2.0   # city breach rate > 2x fleet avg → WARN


# ── Checker ───────────────────────────────────────────────────────────────────

class AnomalyChecker:
    """
    Run a set of targeted QA checks against Silver-layer DataFrames.

    Usage:
        checker = AnomalyChecker()
        report  = checker.check_order_facts(order_facts_df)
        report.print()
    """

    # ── order_facts ───────────────────────────────────────────────────────────

    def check_order_facts(self, df: pd.DataFrame) -> ProfileReport:
        report = ProfileReport(table="silver_order_facts")
        report.findings += self._null_rates(df, ["order_id", "customer_id", "restaurant_id",
                                                   "order_value", "order_ts"])
        report.findings += self._duplicate_keys(df, key_col="order_id")
        report.findings += self._order_value_outliers(df)
        report.findings += self._refund_rate_by_city(df)
        return report

    # ── delivery_ops ──────────────────────────────────────────────────────────

    def check_delivery_ops(self, df: pd.DataFrame) -> ProfileReport:
        report = ProfileReport(table="silver_delivery_ops")
        report.findings += self._null_rates(df, ["order_id", "event_type", "event_ts"])
        report.findings += self._orphan_rate(df)
        report.findings += self._rider_assignment_gaps(df)
        report.findings += self._sla_breach_by_city(df)
        return report

    # ── restaurant_support ────────────────────────────────────────────────────

    def check_restaurant_support(self, df: pd.DataFrame) -> ProfileReport:
        report = ProfileReport(table="silver_restaurant_support")
        report.findings += self._null_rates(df, ["restaurant_id", "city", "cuisine_type"])
        report.findings += self._duplicate_keys(df, key_col="restaurant_id")
        report.findings += self._unresolved_ticket_rate(df)
        return report

    # ── Individual checks ─────────────────────────────────────────────────────

    def _null_rates(self, df: pd.DataFrame, columns: list[str]) -> list[AnomalyFinding]:
        findings = []
        n = len(df)
        if n == 0:
            return findings
        for col in columns:
            if col not in df.columns:
                continue
            null_rate = df[col].isna().sum() / n
            if null_rate >= NULL_RATE_FAIL:
                findings.append(AnomalyFinding(
                    check=f"null_rate[{col}]", severity=FAIL,
                    detail=f"{null_rate:.1%} nulls — exceeds {NULL_RATE_FAIL:.0%} threshold",
                    value=round(null_rate, 4)
                ))
            elif null_rate >= NULL_RATE_WARN:
                findings.append(AnomalyFinding(
                    check=f"null_rate[{col}]", severity=WARN,
                    detail=f"{null_rate:.1%} nulls — exceeds {NULL_RATE_WARN:.0%} threshold",
                    value=round(null_rate, 4)
                ))
            else:
                findings.append(AnomalyFinding(
                    check=f"null_rate[{col}]", severity=OK,
                    detail=f"{null_rate:.1%} nulls", value=round(null_rate, 4)
                ))
        return findings

    def _duplicate_keys(self, df: pd.DataFrame, key_col: str) -> list[AnomalyFinding]:
        if key_col not in df.columns:
            return []
        dup_count = df[key_col].duplicated().sum()
        if dup_count > 0:
            return [AnomalyFinding(
                check=f"duplicates[{key_col}]", severity=WARN,
                detail=f"{dup_count:,} duplicate {key_col} values found",
                value=dup_count
            )]
        return [AnomalyFinding(
            check=f"duplicates[{key_col}]", severity=OK,
            detail="no duplicates", value=0
        )]

    def _order_value_outliers(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if "order_value" not in df.columns:
            return []
        vals = df["order_value"].dropna()
        if len(vals) < 10:
            return []
        mean, std = vals.mean(), vals.std()
        if std == 0:
            return []
        outliers = ((vals - mean).abs() / std > OUTLIER_ZSCORE).sum()
        pct = outliers / len(vals)
        severity = WARN if pct > 0.01 else OK
        return [AnomalyFinding(
            check="order_value_outliers",
            severity=severity,
            detail=f"{outliers:,} orders ({pct:.2%}) beyond {OUTLIER_ZSCORE}σ "
                   f"(mean=₹{mean:.0f}, std=₹{std:.0f})",
            value=int(outliers)
        )]

    def _refund_rate_by_city(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if not {"city", "has_refund"}.issubset(df.columns):
            return []
        fleet_rate = df["has_refund"].mean()
        if fleet_rate == 0:
            return []
        city_rates = df.groupby("city")["has_refund"].mean()
        spikes = city_rates[city_rates > fleet_rate * REFUND_RATE_MULTIPLIER]
        if spikes.empty:
            return [AnomalyFinding(check="refund_rate_by_city", severity=OK,
                                   detail=f"fleet avg {fleet_rate:.1%}, no city anomalies")]
        details = ", ".join(f"{c}: {r:.1%}" for c, r in spikes.items())
        return [AnomalyFinding(
            check="refund_rate_by_city", severity=WARN,
            detail=f"cities > 2x fleet avg ({fleet_rate:.1%}): {details}",
            value={c: round(r, 4) for c, r in spikes.items()}
        )]

    def _orphan_rate(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if "_dq_orphan_order" not in df.columns:
            return []
        n = len(df)
        if n == 0:
            return []
        rate = df["_dq_orphan_order"].sum() / n
        severity = FAIL if rate >= ORPHAN_RATE_FAIL else (WARN if rate > 0 else OK)
        return [AnomalyFinding(
            check="orphan_events",
            severity=severity,
            detail=f"{rate:.2%} of events have no matching order ({df['_dq_orphan_order'].sum():,} rows)",
            value=round(rate, 4)
        )]

    def _rider_assignment_gaps(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if not {"event_type", "rider_id"}.issubset(df.columns):
            return []
        delivery_events = df[df["event_type"].isin(["rider_assigned", "rider_picked_up",
                                                      "out_for_delivery", "delivered"])]
        if len(delivery_events) == 0:
            return []
        missing = delivery_events["rider_id"].isna().sum()
        pct = missing / len(delivery_events)
        severity = FAIL if pct > 0.05 else (WARN if pct > 0 else OK)
        return [AnomalyFinding(
            check="rider_assignment_gaps",
            severity=severity,
            detail=f"{missing:,} delivery events ({pct:.2%}) missing rider_id",
            value=int(missing)
        )]

    def _sla_breach_by_city(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if not {"city", "is_sla_breached"}.issubset(df.columns):
            return []
        # Only consider delivered events
        delivered = df[df["event_type"] == "delivered"] if "event_type" in df.columns else df
        if len(delivered) == 0:
            return []
        fleet_breach = delivered["is_sla_breached"].mean()
        city_breach = delivered.groupby("city")["is_sla_breached"].mean()
        spikes = city_breach[city_breach > fleet_breach * SLA_BREACH_MULTIPLIER]
        if spikes.empty:
            return [AnomalyFinding(check="sla_breach_by_city", severity=OK,
                                   detail=f"fleet avg breach rate {fleet_breach:.1%}")]
        details = ", ".join(f"{c}: {r:.1%}" for c, r in spikes.items())
        return [AnomalyFinding(
            check="sla_breach_by_city", severity=WARN,
            detail=f"cities > 2x fleet breach avg ({fleet_breach:.1%}): {details}",
            value={c: round(r, 4) for c, r in spikes.items()}
        )]

    def _unresolved_ticket_rate(self, df: pd.DataFrame) -> list[AnomalyFinding]:
        if "resolution_status" not in df.columns:
            return []
        tickets = df.dropna(subset=["resolution_status"])
        if len(tickets) == 0:
            return []
        unresolved_rate = (tickets["resolution_status"] != "resolved").mean()
        severity = WARN if unresolved_rate > 0.3 else OK
        return [AnomalyFinding(
            check="unresolved_ticket_rate",
            severity=severity,
            detail=f"{unresolved_rate:.1%} of support tickets unresolved",
            value=round(unresolved_rate, 4)
        )]
