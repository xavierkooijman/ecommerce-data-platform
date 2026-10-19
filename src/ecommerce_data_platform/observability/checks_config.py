from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate,
)
from ecommerce_data_platform.observability.models import CheckConfig
from ecommerce_data_platform.types import SourceTable

CHECK_CONFIG: dict[SourceTable, list[CheckConfig]] = {
    SourceTable.CUSTOMERS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate, threshold=0.05),
    ],
    SourceTable.PRODUCTS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate, threshold=0.05),
    ],
    SourceTable.ORDERS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate, threshold=0.05),
    ],
    SourceTable.ORDER_ITEMS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate, threshold=0.05),
    ],
    SourceTable.SHIPMENTS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate, threshold=0.05),
    ],
}