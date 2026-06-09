# -*- coding: utf-8 -*-
"""
stock_move_category_report.py
==============================
Read-only reporting model backed by a PostgreSQL VIEW.

Design decisions
----------------
* _auto = False  →  Odoo does NOT create a table; we create the VIEW ourselves
  inside init().
* No stored fields are added to any existing Odoo model (stock.move,
  product.product, etc.).  All joins happen at query time inside the VIEW.
* The WHERE clause limits rows to ``state = 'done'`` so the report only shows
  completed stock movements.  The ``state`` field is therefore NOT exposed on
  the model — every visible record already satisfies that condition.
* Read-only access is enforced exclusively through ir.model.access.csv (ACLs).
  Odoo's ORM honours perm_write=0/perm_create=0/perm_unlink=0 automatically;
  overriding create/write/unlink in Python is unnecessary and non-idiomatic.
* product_category is NOT joined in the SQL view.  We select ``pt.categ_id``
  directly from product_template, which already holds the FK.  Adding a JOIN
  to product_category would waste I/O without providing any new columns.
* The primary key is ``sm.id`` (stable, indexed, no ROW_NUMBER() or UUID).
  This guarantees correct drill-down behaviour in Odoo's pivot and list views.
* company_id is exposed for multi-company filtering via standard Odoo record
  rules.  No custom SQL filtering based on the current user is added.

SQL Injection note
------------------
The SQL in init() is a fully static DDL string.  No user-supplied data is
ever concatenated into it, so SQL injection is not possible here.

Future extensibility
--------------------
Additional columns (warehouse_id, picking_type_id, salesperson_id, etc.) can
be appended to the SELECT and a matching LEFT JOIN added without redesigning
the model.  Only init() and the field declarations need to change.
"""

from odoo import fields, models, tools


class StockMoveCategoryReport(models.Model):
    """
    Reporting view: Delivered Products by Product Category.

    Backed by the SQL view ``stock_move_category_report``.  Tables joined:
        - stock_move         (sm)   — source of movement data; PK used as id
        - stock_picking      (sp)   — picking header (provides partner_id)
        - product_product    (pp)   — product variant (indexed FK: product_id)
        - product_template   (pt)   — carries categ_id; avoids redundant JOIN
                        to product_category

    Joins use only indexed FK columns.  No JOIN to product_category is made
      because ``pt.categ_id`` is selected directly from product_template.  No
      JOIN to stock_move_line is needed because, for done moves in Odoo 13,
      ``stock_move.product_uom_qty`` already stores the moved quantity.
    """

    _name = 'stock.move.category.report'
    _description = 'Delivered Products by Category Report'
    _auto = False          # We manage the DB object ourselves via init()
    _rec_name = 'product_id'
    _order = 'date desc'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    date = fields.Datetime(
        string='Date',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        readonly=True,
    )
    quantity = fields.Float(
      string='Quantity',
      readonly=True,
      help='Delivered quantity from stock_move.product_uom_qty on done moves.',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Transfer / Picking',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer / Partner',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    source_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Source Location',
        readonly=True,
    )
    destination_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination Location',
        readonly=True,
    )
    # NOTE: 'state' is intentionally omitted.  The SQL VIEW already filters
    # WHERE sm.state = 'done', so every record is always in state 'done'.
    # Exposing a constant field would waste bandwidth and confuse users.

    # ------------------------------------------------------------------
    # SQL VIEW
    # ------------------------------------------------------------------

    def init(self):
        """
        Create (or replace) the PostgreSQL VIEW that backs this model.

        The view name follows Odoo's _auto=False convention: model _name with
        dots replaced by underscores → ``stock_move_category_report``.

        Performance notes
        -----------------
        * All joins use indexed FK columns (product_id, picking_id, company_id,
          location_id, location_dest_id, product_tmpl_id, categ_id) so the
          query planner can use existing B-tree indexes on those columns.
        * product_category is NOT joined — ``pt.categ_id`` is selected directly
          from product_template, reducing the number of join operations.
        * No JOIN to stock_move_line is needed.  In Odoo 13, once a move is in
          state = done, stock_move.product_uom_qty stores the moved quantity.
          Reading it directly avoids a full aggregation of stock_move_line.
        * The WHERE clause (state = 'done') leverages the existing partial or
          full index on stock_move.state.
        * No Python loops, no computed stored fields, no dynamic SQL.
        """
        tools.drop_view_if_exists(self.env.cr, 'stock_move_category_report')

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW stock_move_category_report AS (
                SELECT
                    -- Primary key: use the stock_move id directly.
                    -- The view is read-only so no sequence is needed.
                    sm.id                       AS id,

                    -- Timing
                    sm.date                     AS date,

                    -- Product information (resolved via JOIN, no stored fields)
                    sm.product_id               AS product_id,
                    pt.categ_id                 AS product_category_id,

                    -- For done moves in Odoo 13, product_uom_qty is the
                    -- quantity actually moved, so one direct column read is
                    -- enough for reporting and avoids a stock_move_line scan.
                    sm.product_uom_qty          AS quantity,

                    -- Transfer / picking header
                    sm.picking_id               AS picking_id,

                    -- Partner comes from the picking header
                    sp.partner_id               AS partner_id,

                    -- Company
                    sm.company_id               AS company_id,

                    -- Locations (both columns are indexed FKs on stock_move)
                    sm.location_id              AS source_location_id,
                    sm.location_dest_id         AS destination_location_id
                    -- NOTE: sm.state is intentionally omitted from SELECT.
                    -- The WHERE clause already guarantees state = 'done';
                    -- a constant column adds no analytical value.

                FROM stock_move sm

                -- Picking header (needed for partner_id)
                LEFT JOIN stock_picking sp
                    ON sp.id = sm.picking_id

                -- Product variant → template.
                -- product_category is NOT joined: we select pt.categ_id
                -- directly from product_template, which already holds the FK.
                -- This eliminates one join and reduces the execution plan cost.
                INNER JOIN product_product pp
                    ON pp.id = sm.product_id          -- indexed FK
                INNER JOIN product_template pt
                    ON pt.id = pp.product_tmpl_id     -- indexed FK

                -- Report scope: completed movements only
                WHERE sm.state = 'done'
            )
        """)

    # ------------------------------------------------------------------
    # Read-only enforcement
    # ------------------------------------------------------------------
    # Access control is enforced exclusively through ir.model.access.csv:
    #   perm_create = 0, perm_write = 0, perm_unlink = 0
    # Odoo's ORM raises an AccessError automatically when those flags are 0.
    # Overriding create/write/unlink in Python is therefore unnecessary and
    # goes against standard Odoo design conventions for _auto=False models.
