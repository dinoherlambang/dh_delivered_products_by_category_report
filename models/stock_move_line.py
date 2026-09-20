# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    picking_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='picking_id.partner_id',
        store=True,
        readonly=True,
        index=True,
        help='Customer / Partner from the delivery order or transfer.',
    )
