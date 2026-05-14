from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Transaction(models.Model):
    _name = 'dreezel.transaction'
    _description = 'Transaksi Penjualan'
    _order = 'date desc, name desc'

    name = fields.Char(string='No. Transaksi', readonly=True, copy=False, default='New')
    cashier_id = fields.Many2one(
        'res.users', string='Kasir', required=True,
        default=lambda self: self.env.user
    )
    date = fields.Datetime(string='Tanggal', required=True, default=fields.Datetime.now, copy=False)
    item_ids = fields.One2many('dreezel.transaction.item', 'transaction_id', string='Item Pesanan')
    discount_id = fields.Many2one('dreezel.discount', string='Kode Diskon')
    payment_method = fields.Selection([
        ('cash', 'Tunai'),
        ('debit', 'Debit'),
        ('e_wallet', 'E-Wallet'),
    ], string='Metode Pembayaran')
    subtotal = fields.Float(
        compute='_compute_totals', store=True, string='Subtotal', digits=(16, 2)
    )
    discount_amount = fields.Float(
        compute='_compute_totals', store=True, string='Jumlah Diskon', digits=(16, 2)
    )
    total = fields.Float(
        compute='_compute_totals', store=True, string='Total', digits=(16, 2)
    )
    amount_paid = fields.Float(string='Jumlah Dibayar', digits=(16, 2))
    change = fields.Float(
        compute='_compute_change', store=True, string='Kembalian', digits=(16, 2)
    )
    # Hanya dua status: Draft dan Lunas
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Lunas'),
    ], string='Status', default='draft', required=True, copy=False)
    note = fields.Text(string='Catatan')

    @api.depends('item_ids.subtotal', 'discount_id', 'discount_id.discount_type', 'discount_id.value')
    def _compute_totals(self):
        for rec in self:
            subtotal = sum(rec.item_ids.mapped('subtotal'))
            rec.subtotal = subtotal
            discount_amount = 0.0
            if rec.discount_id and rec.discount_id.is_active:
                if rec.discount_id.discount_type == 'percentage':
                    discount_amount = subtotal * (rec.discount_id.value / 100.0)
                else:
                    discount_amount = rec.discount_id.value
            rec.discount_amount = discount_amount
            rec.total = subtotal - discount_amount

    @api.depends('total', 'amount_paid')
    def _compute_change(self):
        for rec in self:
            rec.change = rec.amount_paid - rec.total

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dreezel.transaction') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.ensure_one()

        # Bersihkan baris kosong
        self.item_ids.filtered(lambda l: not l.product_id).unlink()

        if not self.item_ids:
            raise UserError('Tambahkan minimal satu produk sebelum konfirmasi pembayaran.')
        if not self.payment_method:
            raise UserError('Pilih metode pembayaran terlebih dahulu.')

        # Debit dan E-Wallet: amount_paid = total secara otomatis
        if self.payment_method in ('debit', 'e_wallet'):
            self.amount_paid = self.total
        elif self.amount_paid < self.total:
            raise UserError(
                f'Jumlah dibayar (Rp {self.amount_paid:,.0f}) '
                f'kurang dari total (Rp {self.total:,.0f}).'
            )

        # Validasi stok bahan baku
        for item in self.item_ids:
            for recipe in item.product_id.ingredient_ids:
                needed = recipe.quantity * item.quantity
                if recipe.ingredient_id.stock < needed:
                    raise ValidationError(
                        f'Stok {recipe.ingredient_id.name} tidak cukup.\n'
                        f'Dibutuhkan: {needed:.2f} {recipe.ingredient_id.unit}\n'
                        f'Tersedia:   {recipe.ingredient_id.stock:.2f} {recipe.ingredient_id.unit}'
                    )

        # Kurangi stok dan buat notifikasi stok menipis
        for item in self.item_ids:
            for recipe in item.product_id.ingredient_ids:
                needed = recipe.quantity * item.quantity
                recipe.ingredient_id.stock -= needed
                if recipe.ingredient_id.is_low_stock:
                    self.env['dreezel.notification'].create({
                        'notification_type': 'low_stock',
                        'title': f'Stok Rendah: {recipe.ingredient_id.name}',
                        'message': (
                            f'Stok {recipe.ingredient_id.name} tersisa '
                            f'{recipe.ingredient_id.stock:.2f} {recipe.ingredient_id.unit}. '
                            f'Segera lakukan pemesanan.'
                        ),
                        'ingredient_id': recipe.ingredient_id.id,
                    })

        self.write({'state': 'paid'})

    def action_kembali_beranda(self):
        """Kembali ke Dashboard POS setelah pembayaran lunas."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard POS',
            'res_model': 'dreezel.transaction',
            'view_mode': 'kanban,tree,form',
            'domain': [('state', 'in', ['draft', 'paid'])],
            'context': {'search_default_today': 1},
            'target': 'current',
        }


class TransactionItem(models.Model):
    _name = 'dreezel.transaction.item'
    _description = 'Item Transaksi'

    transaction_id = fields.Many2one(
        'dreezel.transaction', string='Transaksi', required=True, ondelete='cascade'
    )
    # Tidak required di model — validasi dilakukan di action_confirm
    product_id = fields.Many2one(
        'dreezel.product', string='Produk', ondelete='restrict'
    )
    product_name = fields.Char(related='product_id.name', string='Nama Produk', store=True)
    price_unit = fields.Float(
        string='Harga Satuan', digits=(16, 2), compute='_compute_price_unit', store=True
    )
    quantity = fields.Float(string='Qty', required=True, default=1.0, digits=(16, 2))
    subtotal = fields.Float(
        string='Subtotal', compute='_compute_subtotal', store=True, digits=(16, 2)
    )
    note = fields.Char(string='Catatan')

    @api.depends('product_id')
    def _compute_price_unit(self):
        for rec in self:
            rec.price_unit = rec.product_id.price if rec.product_id else 0.0

    @api.depends('price_unit', 'quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.price_unit * rec.quantity
