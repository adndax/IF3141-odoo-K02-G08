from odoo import models, fields


class Product(models.Model):
    _name = 'dreezel.product'
    _description = 'Product'
    _order = 'name'

    name = fields.Char(string='Product Name', required=True)
    code = fields.Char(string='Code')
    category_id = fields.Many2one('dreezel.category', string='Category', ondelete='set null')
    price = fields.Float(string='Price', required=True, digits=(16, 2))
    description = fields.Text(string='Description')
    is_available = fields.Boolean(string='Available', default=True)
    image = fields.Image(string='Image', max_width=1024, max_height=1024)
    ingredient_ids = fields.One2many(
        'dreezel.product.ingredient', 'product_id', string='Ingredients'
    )


class ProductIngredient(models.Model):
    _name = 'dreezel.product.ingredient'
    _description = 'Product Ingredient'

    product_id = fields.Many2one(
        'dreezel.product', string='Product', required=True, ondelete='cascade'
    )
    ingredient_id = fields.Many2one(
        'dreezel.ingredient', string='Ingredient', required=True, ondelete='restrict'
    )
    quantity = fields.Float(string='Quantity', required=True, digits=(16, 3), default=1.0)
    unit = fields.Char(related='ingredient_id.unit', string='Unit', readonly=True)
