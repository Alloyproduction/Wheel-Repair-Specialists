from odoo import api,tools,fields, models,_
import base64
from odoo import modules

class partnerinherit(models.Model):
    _inherit ='res.partner'

    jobcard_no= fields.Char('JobCard No')
    customer_arabic_name = fields.Char('')
    customer_code = fields.Char()
    is_agency = fields.Boolean('Agency')
    is_service_provider = fields.Boolean('Service Provider')



class InheritSale(models.Model):
    _inherit = 'sale.order'

    vehicle= fields.Many2one('vehicle')
    claim_no = fields.Char('Claim#')
    is_insured = fields.Boolean('insured',default=False)
    service_advisor = fields.Many2one('res.partner',string='Service Advisor')


    @api.onchange('vehicle')
    def onchage_vehicle(self):
        if self.vehicle and self.vehicle.is_insured:
            self.is_insured =True
    @api.one
    @api.constrains('claim_no')
    def unique_identity(self):
        if self.claim_no:
            identities = self.env['sale.order'].search_count([('claim_no', '=', self.claim_no)])
            if identities > 1:
                raise ValueError(_('This claim_no is already exist'))


