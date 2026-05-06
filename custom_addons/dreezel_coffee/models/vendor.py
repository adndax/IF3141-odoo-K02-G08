from odoo import models, fields


class Vendor(models.Model):
    _name = 'dreezel.vendor'
    _description = 'Vendor'
    _order = 'name'

    name = fields.Char(string='Vendor Name', required=True)
    address = fields.Char(string='Address')
    contact = fields.Char(string='Contact')
    is_active = fields.Boolean(string='Active', default=True)
    ingredient_ids = fields.One2many('dreezel.ingredient', 'vendor_id', string='Supplied Ingredients')
