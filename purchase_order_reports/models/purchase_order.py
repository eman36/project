# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from odoo.osv import expression


class ResCompany(models.Model):
    _inherit = "res.company"
    other_condition = fields.Text(string='Default Other Conditions', translate=True)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    other_condition = fields.Text(related='company_id.other_condition', string="Other Conditions", readonly=False)
    use_other_conditions = fields.Boolean(
        string='Default Other Conditions',
        config_parameter='purchase_order_reports.use_other_conditions')



class SaleOrder(models.Model):
    _inherit = 'sale.order'
    customer_po=fields.Char(readonly=True,states={'draft': [('readonly', False)]})
    def name_get(self):
        res = []
        for order in self:
               if order.project_num != 'New':
                  name = order.name+'['+order.project_num+']'
                  res.append((order.id, name))
               else:
                  res=super(SaleOrder, self).name_get()
        return res



    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
           domain = expression.AND([
                    args or [],
                    ['|','|', ('name', operator, name), ('partner_id.name', operator, name), ('project_num', operator, name)]
                ])
           if domain:
                order_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
                return models.lazy_name_get(self.browse(order_ids).with_user(name_get_uid))
           else:
                return super(SaleOrder, self)._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    division_type = fields.Selection(string="Division", selection=[('pct', 'PCT'),
                                                              ('pha', 'PHA'),
                                                              ('text', 'TEX'),
                                                              ('apt', 'APT')],required=True)


    div_check=fields.Boolean()
    # supplier_referance=fields.Char(readonly=True,states={'draft': [('readonly', False)])
    attention_id=fields.Many2one('attention.model.po',readonly=True,states={'draft': [('readonly', False)]})
    delivery_term=fields.Many2one('delivery.term',readonly=True,states={'draft': [('readonly', False)]})
    delivery_time=fields.Many2one('delivery.time',readonly=True,states={'draft': [('readonly', False)]})
    documents_required=fields.Many2many('documents.required','doc','po',readonly=True,states={'draft': [('readonly', False)]})
    project_no=fields.One2many('project.no','p_order',readonly=True,states={'draft': [('readonly', False)]})


    total_EX_Work=fields.Float(compute='calculate_total',store=True)
    total=fields.Float(compute='calculate_total',store=True)
    free_delivery_charges =fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    packing=fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    certificate_of_origin=fields.Float(string='Certificate of Origin / EUR 1',readonly=True,states={'draft': [('readonly', False)]})
    coo=fields.Float(string='C.O.O.',readonly=True,states={'draft': [('readonly', False)]})
    legalization_fees=fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    freight=fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    insurance=fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    shipping=fields.Float(readonly=True,states={'draft': [('readonly', False)]})
    fob_handling=fields.Float(string='FOB Handling',readonly=True,states={'draft': [('readonly', False)]})
    user_confirm_order=fields.Many2one('res.users',tracking=True,copy=False)
    def button_confirm(self):
        res=super(PurchaseOrder, self).button_confirm()
        for rec in self:
            rec.user_confirm_order=self.env.user
        return res

    @api.model
    def _default_other_condition(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'purchase_order_reports.use_other_conditions') and self.env.company.other_condition or ''

    other_condition=fields.Text(default =_default_other_condition)
    @api.constrains('freight','coo','free_delivery_charges', 'fob_handling', 'packing', 'certificate_of_origin','legalization_fees','insurance','shipping')
    def not_mins_float(self):
        for rec in self:
            if rec.shipping < 0.0:
                raise ValidationError(_('Shipping should not be less than Zero'))
            if rec.insurance < 0.0:
                raise ValidationError(_('Insurance should not be less than Zero'))
            if rec.legalization_fees < 0.0:
                raise ValidationError(_('Legalization Fees should not be less than Zero'))
            if rec.certificate_of_origin < 0.0:
                raise ValidationError(_('Certificate of Origin / EUR 1 should not be less than Zero'))
            if rec.freight < 0.0:
                raise ValidationError(_('Freight should not be less than Zero'))
            if rec.coo < 0.0:
                raise ValidationError(_('C.O.O. should not be less than Zero'))
            if rec.free_delivery_charges < 0.0:
                raise ValidationError(_('Free Delivery Charges should not be less than Zero'))
            if rec.fob_handling < 0.0:
                raise ValidationError(_('FOB Handling should not be less than Zero'))
            if rec.packing < 0.0:
                raise ValidationError(_('Packing Handling should not be less than Zero'))



    @api.depends('freight','coo','free_delivery_charges', 'fob_handling','amount_untaxed', 'packing', 'certificate_of_origin','legalization_fees','insurance','shipping')
    def calculate_total(self):
        for rec in self:
            rec.total_EX_Work=rec.amount_untaxed
            rec.total=rec.amount_untaxed+rec.freight+rec.coo+rec.fob_handling+rec.free_delivery_charges+rec.packing+rec.certificate_of_origin+rec.legalization_fees+rec.insurance+rec.shipping

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            year=datetime.now().strftime('%y')
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            if vals.get('material_reuest',False) == False:
                 vals['name'] ='PO'+str(year)+(self.env['ir.sequence'].next_by_code('material.request', sequence_date=seq_date) or '/')+'/'+dict(self._fields['division_type'].selection).get(vals.get('division_type',False))+'/'+self.env['res.partner'].browse(vals.get('partner_id',False)).name.strip().split(' ')[0]

            else:
                 vals['name'] ='MR'+str(year)+(self.env['ir.sequence'].next_by_code('material.request', sequence_date=seq_date) or '/')+'/'+dict(self._fields['division_type'].selection).get(vals.get('division_type',False))+'/'+self.env['res.partner'].browse(vals.get('partner_id',False)).name.strip().split(' ')[0]
        vals['div_check']=True
        return super(PurchaseOrder, self).create(vals)
    def write(self,vals):
        res=super(PurchaseOrder, self).write(vals)
        for rec in self:
          print(self.name.strip().split('/')[:-1])
          if vals.get('partner_id'):
            sequence=''
            for s in self.name.strip().split('/')[:-1]:
                sequence += s+'/'

            rec.name=sequence+rec.partner_id.name.strip().split(' ')[0]
        return res


class AttentionModelPo(models.Model):
    _name = 'attention.model.po'
    name=fields.Char(required=True)
    phone=fields.Char()
    email=fields.Char()
    partner_id=fields.Many2one('res.partner',string='Supplier')

class DeliveryTerm(models.Model):
    _name = 'delivery.term'
    name=fields.Char(required=True)
class DeliveryTime(models.Model):
    _name = 'delivery.time'
    name=fields.Char(required=True)

class DocumentsRequired(models.Model):
    _name = 'documents.required'
    name=fields.Char(required=True)

class ProjectNo(models.Model):
    _name = 'project.no'
    order=fields.Many2one('sale.order',required=True)
    p_order=fields.Many2one('purchase.order')
    sn=fields.Char()
    model=fields.Char(compute='cal_model',store=True)
    _sql_constraints = [
        ('name_order', 'unique()', 'Project No must be unique !'),
    ]


    @api.constrains('order','p_order')
    def unique_project_no(self):
        for rec in self:
            p=self.env['project.no'].search([('order','=',rec.order.id),('p_order','=',rec.p_order.id),('id','!=',rec.id)])
            if p:
                raise ValidationError(_('Project No must be unique !'))
    @api.depends('order')
    def cal_model(self):
        for rec in self :
            product=[]
            for l in rec.order.order_line:
                product.append(l.product_id.model)
            if len(product) > 0:
                rec.model=product[0]



    # def _get_project_no(self):
    #     package_selection = []
    #     sales=self.env['sale.order'].search([('state','=','create_final_guarantee')])
    #     for so in sales:
    #         package_selection.append((so.project_num,so.project_num))
    #     return package_selection


class PurchaseOrderline(models.Model):
    _inherit = 'purchase.order.line'

    sale_order = fields.Many2one('sale.order',string='Order')

    @api.model
    def create(self,vals):
        res=super(PurchaseOrderline, self).create(vals)
        for rec in res:
           rec.sale_order.write({'po':rec.order_id.id})
        return res

    def write(self,vals):
        res=super(PurchaseOrderline, self).write(vals)
        for rec in self:
           rec.sale_order.write({'po':rec.order_id.id})
        return res

    @api.onchange('product_id','sale_order','order_id')
    def onchange_product_id(self):
        res=super(PurchaseOrderline, self).onchange_product_id()
        projects=[]
        if not self.product_id:
            res = {'domain': {}}
            sale = []
            for s in self.order_id.project_no.order:
                sale.append(s.id)
            domains = [('id', 'in', sale)]
            res['domain'].update({'sale_order': domains})
            if self.sale_order:
                products=[]
                for rec in self.sale_order.order_line:
                    if rec.is_delivery == False:
                         products.append(rec.product_id.id)
                domains = [('id', 'in', products)]
                res['domain'].update({'product_id': domains})
            else:
                products = []
                for rec in self.env['product.product'].search([]):
                    products.append(rec.id)
                domains = [('id', 'in', products)]
                res['domain'].update({'product_id': domains})
            return res



        else:
            return res








