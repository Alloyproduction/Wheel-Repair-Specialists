from odoo import api,tools,fields, models,_
import base64
from odoo import modules
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class tasks(models.Model):

    _inherit = 'project.task'

    sale = fields.Char('sale.order')
    sub_component_sale = fields.One2many('subtask.component','task')


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


    @api.model
    def create_task(self,project_id):
        task = self.env['project.task'].create({'name':self.partner_id.name+'-'+self.name,'sale':self.id,'project_id':project_id})

        for line in self.order_line:
            print (line.product_id.name)
            self.env['subtask.component'].create({'task':task.id,'product_id':line.product_id.id,'price_subtotal':line.price_subtotal,'product_uom_qty':line.product_uom_qty,'price_unit':line.price_unit})

    @api.multi
    def action_confirm_replica(self):

        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.project:
            self.create_task(self.project.id)

