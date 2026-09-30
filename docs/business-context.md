# Business Context

## Overview

This project models the data platform of an e-commerce company.

The business operates an OLTP PostgreSQL database supporting customers, products, orders, order items, and shipments.

The data platform serves operational reporting and business intelligence use cases.

## Stakeholders

The platform serves three primary stakeholder groups:

### Operations

Responsible for monitoring order activity, shipment progress, and overall platform performance.

Typical questions include:

- How many orders were placed today?
- How many orders are currently pending?
- How many shipments are delayed?
- What is the current status of an order?

### Finance

Responsible for revenue reporting and product performance analysis.

Typical questions include:

- How much revenue did we generate today?
- How does revenue compare to previous periods?
- Which countries generate the most revenue?
- Which products generate the most revenue?
- Which product categories perform best?

### Customer Support

Responsible for answering customer questions about order and shipment status.

Typical questions include:

- What is the current status of a customer's order?
- Has an order shipped?
- What shipment is associated with a specific order?
- When was an order last updated?

## Historical Reporting Requirements

Not all entities require the same level of historical tracking.

### Customers

Historical customer attributes are required.

Example questions:

- What country was a customer located in when they placed an order?
- How have customer attributes changed over time?

Because these questions require reconstructing past states, customer history must be preserved.

### Products

Current product attributes are sufficient.

Historical product pricing is already captured within order records through the sale price recorded at the time of purchase.

Historical product-category reporting is not currently a business requirement.

### Orders

Only the current order state is required.

The business does not currently require reconstruction of historical order-status transitions.

Example:

The business needs to know:

- What is the order status now?

The business does not currently need to know:

- What was the order status three weeks ago?

## Data Freshness Requirements
 
| Table         | Cadence         | Rationale |
|---------------|-----------------|-----------|
| `customers`   | Every 6 hours   | Profile changes are rare and low-urgency, but same-day support issues shouldn't wait a full day. |
| `products`    | Every 6 hours   | Same reasoning - infrequent changes, same-day correction still matters. |
| `orders`      | Every 5 minutes | Highest-frequency, highest business value. |
| `order_items` | Every 5 minutes | Always loaded with `orders` - meaningless independently. |
| `shipments`   | Every 15 minutes| Delivery delays matter operationally but less urgently than order placement. |