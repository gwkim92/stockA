alter table market.fund_metric_snapshot
    add column if not exists measurement_window text not null default '';

alter table market.fund_metric_snapshot
    add column if not exists measurement_basis text not null default '';

alter table market.fund_metric_snapshot
    add column if not exists benchmark_name text not null default '';

alter table market.fund_metric_snapshot
    add column if not exists fund_return numeric(18,8);

alter table market.fund_metric_snapshot
    add column if not exists benchmark_return numeric(18,8);

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
            'premium_discount_to_nav',
            'tracking_difference_nav_1_month',
            'tracking_difference_nav_qtd',
            'tracking_difference_nav_ytd',
            'tracking_difference_nav_1_year',
            'tracking_difference_nav_3_year',
            'tracking_difference_nav_5_year',
            'tracking_difference_nav_10_year',
            'tracking_difference_nav_since_inception'
        )
    );

alter table market.fund_metric_snapshot
    add constraint fund_metric_snapshot_metric_unit_check
    check (
        (
            metric_code in (
                'gross_expense_ratio',
                'net_expense_ratio',
                'premium_discount_to_nav',
                'tracking_difference_nav_1_month',
                'tracking_difference_nav_qtd',
                'tracking_difference_nav_ytd',
                'tracking_difference_nav_1_year',
                'tracking_difference_nav_3_year',
                'tracking_difference_nav_5_year',
                'tracking_difference_nav_10_year',
                'tracking_difference_nav_since_inception'
            )
            and metric_unit = 'ratio'
        )
        or
        (metric_code in ('nav_per_share', 'bid_ask_midpoint', 'closing_price') and metric_unit = 'USD')
    );

alter table market.fund_metric_snapshot
    add constraint fund_metric_snapshot_metric_value_check
    check (
        (
            metric_code in (
                'premium_discount_to_nav',
                'tracking_difference_nav_1_month',
                'tracking_difference_nav_qtd',
                'tracking_difference_nav_ytd',
                'tracking_difference_nav_1_year',
                'tracking_difference_nav_3_year',
                'tracking_difference_nav_5_year',
                'tracking_difference_nav_10_year',
                'tracking_difference_nav_since_inception'
            )
            and metric_value > -1
            and metric_value < 1
        )
        or
        (
            metric_code not in (
                'premium_discount_to_nav',
                'tracking_difference_nav_1_month',
                'tracking_difference_nav_qtd',
                'tracking_difference_nav_ytd',
                'tracking_difference_nav_1_year',
                'tracking_difference_nav_3_year',
                'tracking_difference_nav_5_year',
                'tracking_difference_nav_10_year',
                'tracking_difference_nav_since_inception'
            )
            and metric_value >= 0
        )
    );
