# -*- coding: utf-8 -*-

from odoo import models, fields, api
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError



class invoicetelenoc(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'x_studio_field_rgEdd': self.x_studio_field_icWOZ.id,
            'x_studio_car_type': self.vehicle.id,
            'x_studio_job_card_1': self.x_studio_agency_job_card,
            'x_studio_service_advisor': self.service_advisor.id,
            'date_invoice': fields.Date.today(),
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        }
        return invoice_vals

        # 'x_studio_field_rgEdd':order.x_studio_field_icWOZ.id,
