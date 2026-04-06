# from odoo import http
# from odoo.http import request
# import io
# import xlsxwriter
#
# class ExcelProperty(http.controller):
#     http.route('property/excel/report', type='http', auth='user')
#     output=io.BytesIO()
#     workbook = xlsxwriter.workbook(output, {'in_memory':True})
#     worksheet = workbook.add_worksheet('Properties')
#
#     header_format = workbook.add_format({'bold':True, 'bg_color':'#D3D3D3', 'border':1, 'align':'center'})
#     header = ['Name' ,'Postcode' , 'Selling Price' , 'Garden']