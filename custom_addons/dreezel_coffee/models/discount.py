from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Discount(models.Model):
    _name = 'dreezel.discount'
    _description = 'Discount'
    _rec_name = 'code'
    _order = 'date_start desc'

    code = fields.Char(string='Code', required=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Type', required=True, default='percentage')
    value = fields.Float(string='Value', required=True)
    date_start = fields.Date(string='Valid From')
    date_end = fields.Date(string='Valid Until')
    is_active = fields.Boolean(string='Active', default=True)

    @api.constrains('value', 'discount_type')
    def _check_value(self):
        for rec in self:
            if rec.value <= 0:
                raise ValidationError('Discount value must be greater than zero.')
            if rec.discount_type == 'percentage' and rec.value > 100:
                raise ValidationError('Percentage discount cannot exceed 100%.')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Discount code must be unique.'),
    ]
