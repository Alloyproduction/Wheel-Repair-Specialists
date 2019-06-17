# -*- coding: utf-8 -*-
from odoo import http

# class Invoicetelenoc(http.Controller):
#     @http.route('/invoicetelenoc/invoicetelenoc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoicetelenoc/invoicetelenoc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoicetelenoc.listing', {
#             'root': '/invoicetelenoc/invoicetelenoc',
#             'objects': http.request.env['invoicetelenoc.invoicetelenoc'].search([]),
#         })

#     @http.route('/invoicetelenoc/invoicetelenoc/objects/<model("invoicetelenoc.invoicetelenoc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoicetelenoc.object', {
#             'object': obj
#         })