{
    'name': 'Majid Purchase Order Approval',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Sistem approval Purchase Order berdasarkan nilai total',
    'description': """
        Modul custom untuk Odoo 18 yang menambahkan sistem approval Purchase Order berdasarkan nilai total dengan email notification di setiap tahap approval.
        
        Fitur:
            - Approval workflow berdasarkan nilai total PO
            - State management yang lebih spesifik
            - Role-based access control
            - Email notification untuk setiap tahap approval
            - Logging aktivitas approval di chatter
            - Dashboard untuk monitoring approval
    """,
    'author': 'Majid',
    'website': 'https://id.linkedin.com/in/adha-syah-majid-7a6b12197',
    'depends': [
        'base',
        'purchase',
        'mail',
    ],
    'data': [
        'security/purchase_approval_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/purchase_order_views.xml',
        'views/res_users_views.xml',
        'wizard/purchase_rejection_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 