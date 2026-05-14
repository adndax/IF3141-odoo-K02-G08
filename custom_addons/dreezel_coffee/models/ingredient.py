from odoo import models, fields, api


class Ingredient(models.Model):
    _name = 'dreezel.ingredient'
    _description = 'Ingredient'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    unit = fields.Char(string='Unit', required=True)
    stock = fields.Float(string='Stock', default=0.0, digits=(16, 3))
    min_stock = fields.Float(string='Minimum Stock', default=0.0, digits=(16, 3))
    price_per_unit = fields.Float(string='Price per Unit', digits=(16, 2))
    vendor_id = fields.Many2one('dreezel.vendor', string='Vendor', ondelete='cascade')
    is_low_stock = fields.Boolean(
        compute='_compute_is_low_stock', store=True, string='Low Stock'
    )

    @api.depends('stock', 'min_stock')
    def _compute_is_low_stock(self):
        for rec in self:
            rec.is_low_stock = rec.stock <= rec.min_stock
