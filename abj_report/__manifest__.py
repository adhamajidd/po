# custom_invoice_print/__manifest__.py

{
    'name': 'Abajoo Custom Invoice Print',
    'version': '1.0',
    'description': 'Menambahkan opsi print custom untuk invoice (modul accounting).',
    'author': 'Majid Abajoo (disesuaikan oleh Gemini)',
    'website': 'https://www.adhacompany.com',
    'license': 'LGPL-3',
    'depends': [
        # Kita ganti 'base' menjadi 'account' karena kita akan bekerja dengan Invoice
        'account',
    ],
    'data': [
        # Sesuaikan urutan: definisikan report action dulu, baru template-nya
        'reports/custom_invoice_report.xml',
        'reports/custom_invoice_template.xml',
    ],
    'auto_install': False,
    'application': False,
}