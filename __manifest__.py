# -*- coding: utf-8 -*-
{
    'name': 'Delivered Products by Category Report',
    'version': '13.0.1.0.0',
    'summary': 'Reporting module for analyzing delivered products grouped by Product Category',
    'description': """
        Provides a dedicated read-only reporting view (stock.move.category.report)
        backed by a PostgreSQL VIEW that joins stock_move, product_product,
        product_template and product_category at query time.

        No existing Odoo tables are modified and no stored fields are added to
        core models.  The report is accessible from:

            Inventory → Reports → Delivered Products by Category
    """,
    'author': 'DH',
    'category': 'Inventory',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_category_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
