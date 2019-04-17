from odoo import api,tools,fields, models,_
import base64
from odoo import modules
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import  datetime

# import  math
#
# class AccountAnalyticLine(models.Model):
#     _inherit = 'account.analytic.line'
#
#     cost = fields.Float('Labor_cost',compute='get_labor_cost',store=True)
#
#
#     @api.one
#     def get_labor_cost(self):
#         if self.employee_id and self.unit_amount:
#             result = '{0:02.0f}:{1:02.0f}'.format((self.unit_amount * 60)/ 60)
#             print(result)
#             employee = self.env['hr.employee'].search([('id','=',self.employee_id.id)])
#             if employee and employee.timesheet_cost:
#                 self.unit_amount/employee.timesheet_cost


class Account_invoice(models.Model):

    _inherit = 'account.invoice'

    sale_id = fields.Many2one('sale.order')


class tasks(models.Model):

    _inherit = 'project.task'

    sale = fields.Char('sale.order')
    sub_component_sale = fields.One2many('subtask.component','task')

    is_task_finished = fields.Boolean('is_task_finish',compute='change_stage')
    # total_cost = fields.Float('Total Labor Cost', compute='_compute_total_cost')
    #
    #
    #
    # def get_total_labor_cost(self):
    #     if self.timesheet_ids:
    #         pass

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
                {'account_id': account_id_credit,'sale_id':sale.id, 'user_id': 1, 'type': 'out_invoice',
                 'journal_id': sales_journal.id, 'partner_id': partner.id,
                 'payment_term_id': payment_term, 'date_invoice': datetime.datetime.now().date()})

            if invoice_obj:
                for all_line in self.sub_component_sale:
                    analytic_account_tag =[]
                    product = self.get_product_obj(all_line.product_id.id)
                        # create invoices
                    account_id_product = self.get_product_account(invoice_obj, partner.id,
                                                                  product[0])
                    for analytic_accounttag in all_line.analytic_tag_ids:
                        analytic_account_tag.append(analytic_accounttag.id)
                    self.env['account.invoice.line'].create(
                        {'invoice_id': invoice_obj.id, 'account_id': account_id_product[0],
                         'product_id': product[0].id, 'name': all_line.product_id.name,
                         'quantity': all_line.product_uom_qty,
                         'price_unit': all_line.price_unit,'discount':all_line.discount,'analytic_tag_ids':[(6, 0, analytic_account_tag)]})

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

    task = fields.Many2one('project.task',ondelete='cascade', index=True, copy=False, readonly=True)

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'),
                                   required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Float(compute='_compute_amount', string='Total', readonly=True, store=True)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.task:
            task =  self.env['project.task'].search([('id', '=',self._context.get('default_sale'))])
            sale = self.env['sale.order'].search([('id', '=', task.sale),('company_id','=',self.env.user.company_id.id)])
            if not self.product_id:
                return {'domain': {'product_uom': []}}

            vals = {}
            domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
                vals['product_uom'] = self.product_id.uom_id
                vals['product_uom_qty'] = self.product_uom_qty or 1.0

            product = self.product_id.with_context(
                lang=sale.partner_id.lang,
                partner=sale.partner_id,
                quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                date=sale.date_order,
                pricelist=sale.pricelist_id.id,
                uom=self.product_uom.id
            )

            result = {'domain': domain}

            title = False
            message = False
            warning = {}
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result

            self._compute_tax_id(sale)
            if sale.pricelist_id and sale.partner_id:
                vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product,sale), product.taxes_id, self.tax_id, self.env.user.company_id)
            self.update(vals)

            return result

    @api.multi
    def _get_display_price(self, product,sale):

        if sale.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=sale.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=sale.partner_id.id, date=sale.date_order,
                               uom=self.product_uom.id)

        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, sale.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.product_uom_qty,
                                                                                           self.product_uom,
                                                                                           sale.pricelist_id.id)
        if currency != sale.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, sale.pricelist_id.currency_id,
                sale.company_id, sale.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.multi
    def _compute_tax_id(self,sale):

        for line in self:
            fpos = sale.fiscal_position_id or sale.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not self.env.user.company_id or r.company_id == self.env.user.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

    @api.one
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        if self.task:
            sale = self.env['sale.order'].search([('id', '=', self.task.sale)])
            for line in self:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, sale.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=sale.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })


class InheritSale(models.Model):
    _inherit = 'sale.order'

    project= fields.Many2one('project.project',string='Service Type')
    @api.multi
    def action_confirm_replica(self):
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.project:
            stage_id = 1
            stage = self.env['project.task.type'].search([('name','=','New')],limit=1)
            if stage:
                stage_id = stage.id
            task = self.env['project.task'].create(
                {'name': self.partner_id.name + '-' + self.name, 'sale': self.id,'stage_id':stage_id,'project_id': self.project.id})

            for line in self.order_line:
                tax_list=[]
                analytic_account_tag=[]
                for tax in line.tax_id:
                    tax_list.append(tax.id)
                for analytic_accounttag in line.analytic_tag_ids:
                    analytic_account_tag.append(analytic_accounttag.id)
                self.env['subtask.component'].create(
                    {'task': task.id, 'product_id': line.product_id.id, 'price_subtotal': line.price_subtotal,
                     'product_uom': line.product_uom.id, 'product_uom_qty': line.product_uom_qty,
                     'price_unit': line.price_unit,'tax_id':[(6, 0, tax_list)],'discount':line.discount,'analytic_tag_ids':[(6, 0, analytic_account_tag)]})

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

