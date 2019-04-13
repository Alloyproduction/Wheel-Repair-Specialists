from odoo import api,tools,fields, models,_
import base64
from odoo import modules
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import  datetime

class tasks(models.Model):

    _inherit = 'project.task'

    sale = fields.Char('sale.order')
    sub_component_sale = fields.One2many('subtask.component','task')

    is_task_finished = fields.Boolean('is_task_finish',compute='change_stage')


    @api.one
    @api.onchange('stage_id')
    def change_stage(self):
        if self.stage_id:
            print('...........',self.stage_id.name)
            if self.stage_id.name=='Finished':
                self.is_task_finished =True
            else:
                self.is_task_finished =False

    @api.one
    def get_payment_term(self, terms):
        if terms:
            terms_obj = self.env['account.payment.term'].search([('name', '=', terms)])
            return terms_obj

    @api.one
    def get_product_obj(self, product_id):
        if product_id:
                product = self.env['product.product'].search([('id', '=', product_id)])
                return product

    @api.one
    def get_product_account(self, invoice, partner_id, product):
        if product:
            domain = {}
            part = partner_id
            fpos = invoice.fiscal_position_id
            company = self.env.user.company_id
            type = 'out_invoice'

            if not part:
                warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner.'),
                }
                return {'warning': warning}
            else:
                account = self.env['account.invoice.line'].get_invoice_line_account(type, product, fpos, company)
                if account:
                    return account.id

    @api.multi
    def create_invoice(self):
        if self.sale and self.sub_component_sale:

            sale = self.env['sale.order'].search([('id', '=', self.sale)])
            partner = sale.partner_id
            payment_term = 1
            account_id_credit = partner.property_account_receivable_id.id
            sales_journal = self.env['account.journal'].search([], limit=1)
            if sales_journal:
                ValueError(_('Set Sales Journal'))

            invoice_obj = self.env['account.invoice'].create(
                {'account_id': account_id_credit, 'user_id': 1, 'type': 'out_invoice',
                 'journal_id': sales_journal.id, 'partner_id': partner.id,
                 'payment_term_id': payment_term, 'date_invoice': datetime.datetime.now().date()})

            if invoice_obj:
                for all_line in self.sub_component_sale:
                    product = self.get_product_obj(all_line.product_id.id)
                        # create invoices
                    account_id_product = self.get_product_account(invoice_obj, partner.id,
                                                                  product[0])
                    self.env['account.invoice.line'].create(
                        {'invoice_id': invoice_obj.id, 'account_id': account_id_product[0],
                         'product_id': product[0].id, 'name': all_line.product_id.name,
                         'quantity': all_line.product_uom_qty,
                         'price_unit': all_line.price_unit})

            view = self.env.ref('account.invoice_form')
            return {
                'name': 'Invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'res_id': invoice_obj.id,
                'context': self.env.context
            }

    def close_task(self):
        stage = self.env['project.task.type'].search([('name', '=', 'Finished')])
        if stage:
            self.write({'stage_id':stage.id})


class subtaskcomponent(models.Model):

    _name  = 'subtask.component'

    task = fields.Many2one('project.task')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'),
                                   required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    price_subtotal = fields.Float(string='subtotal')


class InheritSale(models.Model):
    _inherit = 'sale.order'

    project= fields.Many2one('project.project',string='Service Type')

    @api.one
    def action_confirm_replica(self):
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.project:
            stage_id = 1
            stage = self.env['project.task.type'].search([('name','=','New')])
            if stage:
                stage_id = stage.id
            task = self.env['project.task'].create(
                {'name': self.partner_id.name + '-' + self.name, 'sale': self.id,'stage_id':stage_id,'project_id': self.project.id})

            for line in self.order_line:
                self.env['subtask.component'].create(
                    {'task': task.id, 'product_id': line.product_id.id, 'price_subtotal': line.price_subtotal,
                     'product_uom': line.product_uom.id, 'product_uom_qty': line.product_uom_qty,
                     'price_unit': line.price_unit})

            view = self.env.ref('project.view_task_form2')
            return {
                'name': 'Task created',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': 'project.task',
                'type': 'ir.actions.act_window',
                'res_id': task.id,
                'context': self.env.context
            }

