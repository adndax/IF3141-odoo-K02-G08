from odoo import models, fields


class Category(models.Model):
    _name = 'dreezel.category'
    _description = 'Product Category'
    _order = 'name'

    name = fields.Char(string='Category', required=True)
    product_ids = fields.One2many('dreezel.product', 'category_id', string='Products')
    product_count = fields.Integer(compute='_compute_product_count', string='Product Count')

    def _compute_product_count(self):
        for rec in self:
            rec.product_count = len(rec.product_ids)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Category name must be unique.'),
    ]
