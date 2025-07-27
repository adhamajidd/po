# ABJ Purchase Order Approval Module

## Deskripsi
Modul ini menambahkan sistem approval otomatis untuk Purchase Order berdasarkan nilai total di Odoo 18.

## Fitur Utama

### 1. Sistem Approval Berdasarkan Nilai Total
- **Kurang dari IDR 5 juta**: Langsung ke Manager
- **IDR 5-20 juta**: Ke Department Head, kemudian ke CFO
- **Lebih dari IDR 20 juta**: Langsung ke CFO

### 2. Button Approval
- **Submit for Approval**: Submit PO untuk approval
- **Approve**: Approve PO pada level saat ini
- **Reject**: Reject PO dengan alasan

### 3. Email Notification
- Email otomatis dikirim ke approver yang sesuai
- Email notification untuk rejection dengan alasan
- Template email yang dapat dikustomisasi

### 4. Logging dan Tracking
- Semua aktivitas approval dicatat di chatter
- Tracking approval state dan level
- History approval dengan timestamp

### 5. Role-Based Access Control
- **Purchase Manager**: Approve PO < IDR 5 juta
- **Department Head**: Approve PO IDR 5-20 juta
- **CFO**: Approve PO > IDR 20 juta

## Instalasi

1. Copy modul ke folder `addons`
2. Update modul list di Odoo
3. Install modul `majid_purchase_approval`
4. Konfigurasi user roles di Settings > Users & Companies > Users

## Konfigurasi

### 1. Setup User Roles
1. Buka Settings > Users & Companies > Users
2. Edit user yang akan menjadi approver
3. Set field "Approval Role" sesuai dengan:
   - **Purchase Manager**: Untuk approve PO < IDR 5 juta
   - **Department Head**: Untuk approve PO IDR 5-20 juta
   - **CFO**: Untuk approve PO > IDR 20 juta

### 2. Setup Email Template (Opsional)
- Template email dapat dikustomisasi di Settings > Technical > Email > Templates
- Template ID: `majid_purchase_approval.email_template_purchase_approval`
- Template ID: `majid_purchase_approval.email_template_purchase_rejection`

## Penggunaan

### 1. Submit PO untuk Approval
1. Buat Purchase Order baru
2. Tambahkan order lines
3. Klik button "Submit for Approval"
4. Sistem akan menentukan approval level berdasarkan nilai total
5. Email notification akan dikirim ke approver yang sesuai

### 2. Approve/Reject PO
1. Approver login ke sistem
2. Buka menu "Purchase > My Purchase Approvals"
3. Pilih PO yang perlu diapprove
4. Klik "Approve" atau "Reject"
5. Jika reject, masukkan alasan rejection

### 3. Tracking Approval
- Status approval dapat dilihat di tab "Approval Information"
- Semua aktivitas dicatat di chatter
- Email notification dikirim untuk setiap tahap

## Field Baru

### Purchase Order
- `approval_state`: Status approval (draft, submitted, manager_approved, dept_head_approved, cfo_approved, rejected, approved)
- `approval_level`: Level approval saat ini (manager, dept_head, cfo)
- `approval_threshold`: Threshold berdasarkan nilai (low, medium, high)
- `submitted_by`: User yang submit untuk approval
- `submitted_date`: Tanggal submit
- `approved_by_manager`: User yang approve sebagai manager
- `approved_by_dept_head`: User yang approve sebagai department head
- `approved_by_cfo`: User yang approve sebagai CFO
- `approved_date_manager`: Tanggal approval manager
- `approved_date_dept_head`: Tanggal approval department head
- `approved_date_cfo`: Tanggal approval CFO
- `rejection_reason`: Alasan rejection
- `rejected_by`: User yang reject
- `rejected_date`: Tanggal rejection

### User
- `approval_role`: Role approval user (none, manager, dept_head, cfo)

## Security Groups

- `group_purchase_manager`: Purchase Manager
- `group_purchase_dept_head`: Department Head
- `group_purchase_cfo`: CFO
- `group_purchase_approval_user`: Purchase Approval User

## Troubleshooting

### 1. Email tidak terkirim
- Pastikan email server dikonfigurasi dengan benar
- Cek email address user approver sudah diisi
- Cek log email di Settings > Technical > Logging

### 2. Button approval tidak muncul
- Pastikan user memiliki role approval yang sesuai
- Cek group membership user
- Pastikan PO dalam status yang benar

### 3. Approval flow tidak berjalan
- Cek nilai total PO
- Pastikan ada user dengan role yang sesuai
- Cek approval state dan level

## Support

Untuk bantuan dan support, silakan hubungi tim development ABJ.

## Version History

- **v1.0**: Initial release dengan fitur approval berdasarkan nilai total 