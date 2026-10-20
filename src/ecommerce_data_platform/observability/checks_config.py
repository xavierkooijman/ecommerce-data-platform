from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate_percentage,
)
from ecommerce_data_platform.observability.models import CheckConfig
from ecommerce_data_platform.types import SourceTable

CHECK_CONFIG: dict[SourceTable, list[CheckConfig]] = {
    SourceTable.CUSTOMERS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    SourceTable.PRODUCTS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    SourceTable.ORDERS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    SourceTable.ORDER_ITEMS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    SourceTable.SHIPMENTS: [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
}