from odoo import api,tools,fields, models,_
import base64
from odoo import modules


class InheritPartner(models.Model):
    _inherit = 'res.partner'

    is_insurance = fields.Boolean(string='Insurance', default=False,
                                help="Check if the contact is a company, otherwise it is a person")

    insurance_company = fields.Many2one('res.partner','Insurance Company')
    chasis_no = fields.Char('Chasis#')
    car_type = fields.Many2one('fleet.vehicle.model','Car Type')
    plate_no = fields.Char('Plate No')
    job_card_no = fields.Char('Jobcard No')
    odoo_meter = fields.Char('Odoometer')
    claim_no = fields.Char('Claim No')
    service_advisor = fields.Char('Service Advisor')
    agency_name = fields.Char('Agency Name')
    source = fields.Char('Source')

