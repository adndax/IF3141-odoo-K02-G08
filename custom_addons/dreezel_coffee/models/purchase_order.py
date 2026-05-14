from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = 'dreezel.purchase.order'
    _description = 'Purchase Order'
    _order = 'date desc, name desc'

    name = fields.Char(string='No. Pesanan', readonly=True, copy=False, default='New')
    vendor_id = fields.Many2one(
        'dreezel.vendor', string='Vendor', required=True, ondelete='restrict'
    )
    date = fields.Date(string='Tanggal Pesanan', required=True, default=fields.Date.today)
    item_ids = fields.One2many('dreezel.purchase.item', 'order_id', string='Item Pesanan')
    total_price = fields.Float(
        compute='_compute_total', store=True, string='Total', digits=(16, 2)
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ordered', 'Dipesan'),
        ('received', 'Diterima'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='draft', required=True, copy=False)
    note = fields.Text(string='Catatan')
    receipt_date = fields.Date(string='Tanggal Terima', readonly=True)
    received_by = fields.Many2one('res.users', string='Diterima Oleh', readonly=True)

    @api.depends('item_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total_price = sum(rec.item_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dreezel.purchase.order') or 'New'
        return super().create(vals_list)

    def action_order(self):
        self.ensure_one()
        # Bersihkan baris kosong sebelum validasi
        self.item_ids.filtered(lambda l: not l.ingredient_id).unlink()
        if not self.item_ids:
            raise UserError('Tambahkan minimal satu bahan baku sebelum memesan.')
        self.write({'state': 'ordered'})

    def action_receive(self):
        self.ensure_one()
        for item in self.item_ids:
            if item.ingredient_id:
                item.ingredient_id.stock += item.quantity
        self.env['dreezel.notification'].create({
            'notification_type': 'goods_arrived',
            'title': f'Barang Diterima: {self.name}',
            'message': (
                f'Pemesanan {self.name} dari {self.vendor_id.name} '
                f'telah diterima pada {fields.Date.today()}.'
            ),
            'order_id': self.id,
        })
        self.write({
            'state': 'received',
            'receipt_date': fields.Date.today(),
            'received_by': self.env.user.id,
        })

    def action_cancel(self):
        """Batalkan pesanan dan kembali ke daftar pemesanan."""
        self.ensure_one()
        if self.state == 'received':
            raise UserError('Pemesanan yang sudah diterima tidak dapat dibatalkan.')

        # Bersihkan baris kosong sebelum menyimpan
        self.item_ids.filtered(lambda l: not l.ingredient_id).unlink()
        self.write({'state': 'cancelled'})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Pemesanan Bahan Baku',
            'res_model': 'dreezel.purchase.order',
            'view_mode': 'tree,form',
            'domain': [('state', 'in', ['draft', 'ordered'])],
            'context': {'search_default_draft': 1},
            'target': 'current',
        }


class PurchaseItem(models.Model):
    _name = 'dreezel.purchase.item'
    _description = 'Purchase Order Item'

    order_id = fields.Many2one(
        'dreezel.purchase.order', string='Pesanan', required=True, ondelete='cascade'
    )
    # Tidak required di model — validasi dilakukan di action_order
    ingredient_id = fields.Many2one(
        'dreezel.ingredient', string='Bahan Baku', ondelete='restrict'
    )
    unit = fields.Char(related='ingredient_id.unit', string='Satuan', readonly=True)
    quantity = fields.Float(string='Jumlah', required=True, default=1.0, digits=(16, 3))
    price_unit = fields.Float(string='Harga Satuan', digits=(16, 2))
    subtotal = fields.Float(
        compute='_compute_subtotal', store=True, string='Subtotal', digits=(16, 2)
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit
