# -*- coding: utf-8 -*-
{
    'name': "POS Custom Logo",
    'summary': "Add custom logo for each POS configuration",
    'description': """
       This module allows each Point of Sale (POS) configuration to use a custom logo
that is displayed on the printed receipt. The logo is set directly in the POS
settings and does not use the default company logo. 
    """,
    'author': "Abajoo",
    'license': 'LGPL-3',
    'category': "Point of Sale",
    'version': "1.0",
    'depends': ['base', 'point_of_sale'],
    'data': [
        'data/ir.model.fields.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'abj_pos_receipt_logo/static/src/js/models.js',
            'abj_pos_receipt_logo/static/src/xml/navbar_logo.xml',
            'abj_pos_receipt_logo/static/src/xml/pos.xml',
            'abj_pos_receipt_logo/static/src/xml/receipt_logo.xml',
            'abj_pos_receipt_logo/static/src/xml/order_line.xml',
        ],
    },
    'installable': True,
}
