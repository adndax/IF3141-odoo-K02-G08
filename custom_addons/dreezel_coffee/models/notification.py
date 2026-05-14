from odoo import models, fields


class Notification(models.Model):
    _name = 'dreezel.notification'
    _description = 'Notification'
    _order = 'date desc'

    notification_type = fields.Selection([
        ('low_stock', 'Low Stock Alert'),
        ('goods_arrived', 'Goods Arrived'),
    ], string='Type', required=True)
    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    is_read = fields.Boolean(string='Read', default=False)
    ingredient_id = fields.Many2one(
        'dreezel.ingredient', string='Ingredient', ondelete='set null'
    )
    order_id = fields.Many2one(
        'dreezel.purchase.order', string='Purchase Order', ondelete='set null'
    )

    def action_mark_read(self):
        self.write({'is_read': True})

    def action_mark_unread(self):
        self.write({'is_read': False})
