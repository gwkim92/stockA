alter table market.fund_metric_snapshot
    drop constraint if exists fund_metric_snapshot_metric_code_check;

alter table market.fund_metric_snapshot
    drop constraint if exists fund_metric_snapshot_metric_unit_check;

alter table market.fund_metric_snapshot
    drop constraint if exists fund_metric_snapshot_metric_value_check;

alter table market.fund_metric_snapshot
    add constraint fund_metric_snapshot_metric_code_check
    check (
        metric_code in (
            'gross_expense_ratio',
            'net_expense_ratio',
            'nav_per_share',
            'bid_ask_midpoint',
            'closing_price',
            'premium_discount_to_nav'
        )
    );

alter table market.fund_metric_snapshot
    add constraint fund_metric_snapshot_metric_unit_check
    check (
        (metric_code in ('gross_expense_ratio', 'net_expense_ratio', 'premium_discount_to_nav') and metric_unit = 'ratio')
        or
        (metric_code in ('nav_per_share', 'bid_ask_midpoint', 'closing_price') and metric_unit = 'USD')
    );

alter table market.fund_metric_snapshot
    add constraint fund_metric_snapshot_metric_value_check
    check (
        (metric_code = 'premium_discount_to_nav' and metric_value > -1 and metric_value < 1)
        or
        (metric_code <> 'premium_discount_to_nav' and metric_value >= 0)
    );
