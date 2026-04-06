import json
from odoo import http
from odoo.http import request




class PropertyApi(http.Controller):
     @http.route("/v1/property",methods=['POST'],type='http',auth='none',csrf=False)
     def post_property(self):
         args=request.httprequest.data.decode()
         vals=json.loads(args)
         if not vals.get('name'):
             return request.make_json_response({
                 'message': 'Name is required'
             }, status=400)
         try:
             res=request.env['property'].creare(vals)
             if res:
                 return request.make_json_response({
                     'message':'successfully',
                     'id':res.id,
                     'name':res.name,
                 },status=200)
         except Exception as error:
            return request.make_json_response({
             'message': error,
         }, status=400)

     @http.route("/v1/property/jso", methods=['POST'], type='json', auth='none', csrf=False)
     def post_property_json(self):
         args = request.httprequest.data.decode()
         vals = json.loads(args)
         print(vals)
         res = request.env['property'].creare(vals)
         if res:
             return({
                 'message': 'successfully'
             })


     @http.route('/v1/property/<int:property_id>',methods=['PUT'], type='json', auth='none', csrf=False)
     def update_property(self,property_id):
         try:
             property_id=request.env['property'].search([('id','=','property_id')])
             if not property_id:
                 return request.make_json_response({
                     'message': "ID dose not exist",
                 }, status=400)
             args=request.httprequest.data.decode()
             vals=json.loads(args)
             property_id.write(vals)
             return request.make_json_response({
                 'message': 'Updating successfully',
                 'id': property_id.id,
                 'name': property_id.name,
             }, status=200)
         except Exception as error:
             return request.make_json_response({
                 'message': error,
             }, status=400)

     @http.route('/v1/property/<int:property_id>',methods=['GET'], type='json', auth='none', csrf=False)
     def get_property(self,property_id):
         try:
             property_id = request.env['property'].search([('id', '=', 'property_id')])
             if property_id:
                 pass
             else:
                 return request.make_json_response({
                     'message': 'There is no property match ID',
                 }, status=400)
             return request.make_json_response({
                 'message': 'Updating successfully',
                 'id': property_id.id,
                 'name': property_id.name,
                 'ref':property_id.ref,
                 'description':property_id.description,
                 'bedrooms':property_id.bedrooms,
             }, status=200)
         except Exception as error:
             return request.make_json_response({
                 'message': error,
             }, status=400)


     @http.route('/v1/property/<int:property_id>',methods=['DELETE'], type='json', auth='none', csrf=False)
     def  delete_property(self,property_id):
         try:
             property_id = request.env['property'].search([('id', '=', 'property_id')])
             if not property_id:
                 return request.make_json_response({
                     'message': "ID dose not exist",
                 }, status=400)
             property_id.unlink()
             return request.make_json_response({
                 'message': 'Deleted successfully',
             }, status=200)
         except Exception as error:
             return request.make_json_response({
                 'message': error,
             }, status=400)

