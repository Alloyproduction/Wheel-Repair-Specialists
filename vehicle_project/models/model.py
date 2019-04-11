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

    @api.multi
    def action_confirm_replica(self):
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.project:
            task = self.env['project.task'].create(
                {'name': self.partner_id.name + '-' + self.name, 'sale': self.id, 'project_id': self.project.id})

            for line in self.order_line:
                print (line.product_id.name)
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

