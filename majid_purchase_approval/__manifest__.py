{
    'name': 'Majid Purchase Order Approval',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Sistem approval Purchase Order berdasarkan nilai total',
    'description': """
        Modul ini menambahkan sistem approval otomatis untuk Purchase Order berdasarkan nilai total:
        - Kurang dari IDR 5 juta: langsung ke Manager
        - IDR 5-20 juta: ke Department Head, kemudian ke CFO
        - Lebih dari IDR 20 juta: langsung ke CFO
        
        Fitur:
        - Button Submit for Approval, Approve, dan Reject
        - Email notification untuk setiap tahap approval
        - Log aktivitas di chatter
        - Role-based access control
    """,
    'author': 'Majid',
    'website': 'https://www.abj.com',
    'depends': [
        'base',
        'purchase',
        'mail',
        'hr',
    ],
    'data': [
        'security/purchase_approval_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/purchase_order_views.xml',
        'views/res_users_views.xml',
        'wizard/purchase_rejection_wizard_views.xml',
    ],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 