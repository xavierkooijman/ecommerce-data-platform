from ecommerce_data_platform.models import DataSource, Resource, SourceSystem
from ecommerce_data_platform.observability.checks import (
    check_consecutive_zero_row_runs,
    check_rejection_rate_percentage,
)
from ecommerce_data_platform.observability.models import CheckConfig

CHECK_CONFIG: dict[DataSource, list[CheckConfig]] = {
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.CUSTOMERS): [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.PRODUCTS): [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.ORDERS): [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.ORDER_ITEMS): [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
    DataSource(SourceSystem.ECOMMERCE_DB, Resource.SHIPMENTS): [
        CheckConfig(check_consecutive_zero_row_runs, threshold=3),
        CheckConfig(check_rejection_rate_percentage, threshold=5),
    ],
}