# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Reports",

    'description': """
         Purchase Order Reports    """,

    'author': "ITSYS-Eman Ahmed",
    'website': "http://www.it-syscorp.com",
    'category': 'sale',
    'version': '13.0.1',
    'depends': ['base','purchase','material_request','letter_guarantee','add_sale_type_sequence','sale','bi_convert_purchase_from_sales'],
    'wbs':'MMS-38',

    'data': [
        'security/ir.model.access.csv',
        'report/header_footer.xml',
        'report/report.xml',
        'report/purchase_order_template.xml',
        'report/MR_template.xml',
        'views/delivery_time.xml',
        'views/delivery_term.xml',
        'views/documents_required.xml',
        'views/attention_model_view.xml',
        'views/purchase_order_view.xml',

    ],

}
