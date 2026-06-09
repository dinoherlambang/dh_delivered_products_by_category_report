# Delivered Products by Category Report

Odoo 13 Community addon that provides a dedicated Inventory report for analyzing delivered products by Product Category without altering Odoo core tables or the standard Stock Moves report.

## Overview

This module adds a new read-only reporting model backed by a PostgreSQL SQL view:

- Model: `stock.move.category.report`
- Menu: Inventory -> Reports -> Delivered Products by Category
- Views: tree, pivot, graph, and search

The report is independent from the standard Inventory reporting screens. It is designed for reporting use cases and does not add stored fields to `stock.move` or any other core model.

## What It Reports

The report only includes completed stock moves:

- `state = 'done'`

Users can analyze delivered quantities by:

- Product Category
- Product
- Month or Year
- Customer
- Company
- Picking / Transfer
- Source and Destination Location

Typical questions this report answers:

- How many Tire products were delivered in 2025?
- Which Tire products had the highest delivered quantity?
- What are the monthly delivered quantities by Product Category?
- Which customers received the most products in a given category?

## Functional Features

- Dedicated report under Inventory Reports
- Read-only reporting model using `_auto = False`
- SQL view created in `init()` with `tools.drop_view_if_exists()`
- Product Category resolved at query time through product relationships
- Tree view for detailed records
- Pivot view for aggregation and drill-down
- Graph view for quick visual analysis
- Search filters for category, product, date, company, customer, transfer, and locations
- Group By options for category, product, customer, company, transfer, year, and month

## Technical Design

The SQL view reads from existing Odoo tables and does not duplicate data.

Main tables used:

- `stock_move`
- `stock_picking`
- `product_product`
- `product_template`

### Why no `product_category` join?

`product_template.categ_id` already stores the Product Category foreign key, so the report reads category directly from `product_template` instead of joining `product_category` only to get the same identifier.

This keeps the query simpler and avoids unnecessary I/O.

### Why no `stock_move_line` aggregation?

For done moves in Odoo 13, `stock_move.product_uom_qty` represents the moved quantity. Because this report is strictly limited to done moves, it can use that value directly as the reporting quantity.

That avoids a full aggregation on `stock_move_line`, which is a better fit for large databases where reporting queries must stay as lean as possible.

## Reported Fields

The report exposes the following main fields:

- Date
- Product Category
- Product
- Quantity
- Picking / Transfer
- Customer
- Company
- Source Location
- Destination Location

## Security

The report follows standard Inventory access patterns:

- Inventory Users can read the report
- Inventory Managers can read the report
- No create, write, or delete permissions are granted

The model is intended to remain read-only.

## Installation

1. Copy this addon into your Odoo custom addons path.
2. Update the app list.
3. Install `Delivered Products by Category Report`.

## Usage

After installation, open:

Inventory -> Reports -> Delivered Products by Category

From there you can:

- review completed delivery movements in list view
- analyze totals in pivot view
- group by category, product, customer, company, or transfer
- filter by month, year, or custom date ranges
- drill down from pivot cells into the underlying stock moves

## Module Structure

```text
dh_delivered_products_by_category_report/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── stock_move_category_report.py
├── security/
│   └── ir.model.access.csv
└── views/
    └── stock_move_category_report_views.xml
```

## Notes

- This module does not modify the standard Stock Moves report.
- This module does not add stored related fields to Odoo core tables.
- This module is designed for Odoo 13 Community.

## License

LGPL-3