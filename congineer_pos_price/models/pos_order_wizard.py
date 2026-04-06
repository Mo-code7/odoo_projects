from odoo import models, api

class PosOrderWizard(models.TransientModel):
    _name = 'pos.order.wizard'
    _description = 'POS Order Wizard'

    @api.model
    def generate_report(self, order_name, lines):
        # نضع البيانات في قاموس ونرسله بوضوح
        data = {
            'order_info': {
                'name': order_name,
                'lines': lines,
            }
        }
        # نمرر False كـ IDs لنتجنب خطأ الـ Index
        return self.env.ref('congineer_pos_price.action_pos_order_report').report_action(None, data=data)

# هذا الكلاس هو "المحرك" الذي يربط البيانات بالـ Template
class ReportPosOrder(models.AbstractModel):
    _name = 'report.congineer_pos_price.pos_order_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        # هنا نخبر أودو: خذ البيانات من الـ data التي أرسلناها
        return {
            'doc_ids': docids,
            'doc_model': 'pos.order.wizard',
            'order_data': data.get('order_info') if data else {},
        }