# Majid Purchase Order Approval Module

Modul custom untuk Odoo 18 yang menambahkan sistem approval Purchase Order berdasarkan nilai total dengan state yang lebih spesifik.

## Fitur Utama

### 1. Approval Workflow Berdasarkan Nilai Total
- **< 5 Juta IDR**: Langsung ke Manager
- **5-20 Juta IDR**: Department Head → CFO
- **> 20 Juta IDR**: Langsung ke CFO

### 2. State Management yang Lebih Spesifik
Modul ini menambahkan state baru ke Purchase Order untuk tracking approval yang lebih detail:

#### State Asli (Tetap Ada):
- `draft` - RFQ (Draft)
- `sent` - RFQ Sent
- `to approve` - To Approve (untuk approval standar)
- `purchase` - Purchase Order (setelah approve)
- `done` - Locked
- `cancel` - Cancelled

#### State Baru (Ditambahkan):
- `manager_approval` - Menunggu approval Manager
- `dept_head_approval` - Menunggu approval Department Head
- `cfo_approval` - Menunggu approval CFO
- `approved` - Sudah di-approve (state tambahan)
- `rejected` - Di-reject (state khusus untuk rejection)

### 3. Button dan Workflow
- **Confirm Order**: Submit untuk approval (menggunakan button standar)
- **Approve**: Approve PO (menggunakan button standar)
- **Reject**: Reject PO dengan alasan

### 4. Email Notifications
- Email otomatis ke approver saat PO di-submit
- Email notifikasi rejection ke submitter

### 5. Chatter Integration
- Log semua aktivitas approval di chatter
- Tracking lengkap approval history

## Instalasi

1. Copy modul ke folder `addons/`
2. Update modul list di Odoo
3. Install modul `majid_purchase_approval`
4. Konfigurasi user roles

## Konfigurasi

### 1. Setup User Roles
Buka **Settings > Users & Companies > Users** dan set field **Approval Role**:
- **Manager**: Untuk approve PO < 5 juta
- **Department Head**: Untuk approve PO 5-20 juta
- **CFO**: Untuk approve PO > 20 juta

### 2. Security Groups
Modul otomatis membuat security groups:
- **Purchase Manager**
- **Department Head** 
- **CFO**
- **Purchase Approval User**

## Penggunaan

### 1. Submit Purchase Order
1. Buat Purchase Order baru
2. Isi order lines dengan total nilai sesuai threshold
3. Klik **Confirm Order**
4. PO akan otomatis masuk ke approval workflow

### 2. Approval Process
1. Approver login ke sistem
2. Buka menu **Purchase > My Purchase Approvals**
3. Pilih PO yang perlu di-approve
4. Klik **Approve** atau **Reject**

### 3. Rejection Process
1. Klik **Reject** button
2. Isi alasan rejection di popup
3. PO akan masuk state `rejected`
4. Email notifikasi dikirim ke submitter

## Testing Email Approval System

### **Skenario Testing Lengkap:**

#### **Step 1: Setup Email Configuration**
1. Buka **Settings > Technical > Email > Outgoing Mail Servers**
2. Tambahkan SMTP server (Gmail, Outlook, atau local SMTP)
3. Test koneksi email

#### **Step 2: Login sebagai Purchase User**
```
Login: demo.purchase
Password: demo123
Email: demo.purchase@example.com
```

#### **Step 3: Buat Purchase Order**
1. Buka **Purchase > Orders > Purchase Orders**
2. Klik **Create**
3. Pilih vendor: **Demo Vendor**
4. Tambahkan product dengan nilai < 5 juta (misal: Demo Product Low Value)
5. Klik **Confirm Order**
6. PO akan masuk state **Manager Approval**

#### **Step 4: Cek Email Approval**
1. Login sebagai Manager:
   ```
   Login: demo.manager
   Password: demo123
   Email: demo.manager@example.com
   ```
2. Buka **Discuss** (chat icon di top menu)
3. Cek **Inbox** untuk email approval
4. Atau buka PO dan lihat di **Chatter** (scroll ke bawah)

#### **Step 5: Approve atau Reject**
1. Buka **Purchase > My Purchase Approvals**
2. Pilih PO yang perlu diapprove
3. Klik **Approve** atau **Reject**
4. Jika reject, isi alasan rejection

#### **Step 6: Cek Email Rejection (jika reject)**
1. Login kembali sebagai Purchase User
2. Buka **Discuss > Inbox**
3. Cek email rejection notification

### **Testing di Database Neutralized (Tanpa Email)**

Jika database di-neutralize untuk testing (tidak ada email), Anda masih bisa testing workflow approval dengan melihat log di chatter:

#### **Step 1: Disable Email Notification**
Jalankan command ini di Odoo shell atau Technical > Parameters:
```python
self.env['ir.config_parameter'].sudo().set_param('majid_purchase_approval.enable_email_notification', 'False')
```

#### **Step 2: Testing Workflow Approval**
1. **Login sebagai Purchase User** → Buat PO → Submit
2. **Buka PO** → Scroll ke bawah → Lihat di **Chatter/Log Note**
3. **Login sebagai Manager** → Buka **My Purchase Approvals** → Approve/Reject
4. **Buka PO lagi** → Lihat log approval di chatter

#### **Step 3: Cek Log di Chatter**
Di chatter akan muncul log seperti:
- ✅ **"Purchase Order di-submit untuk approval Manager oleh Demo Purchase User. Nilai total: IDR 3,000,000, Threshold: low"**
- ✅ **"Purchase Order di-approve oleh Demo Manager (Manager). Final approval - PO menjadi Purchase Order"**
- ✅ **"Purchase Order di-reject oleh Demo Manager (Manager). Alasan: Budget tidak mencukupi"**

### **Cara Memberitahu Approver Tanpa Email:**

#### **1. Menu "My Purchase Approvals" (Paling Efektif)**
- **Purchase > My Purchase Approvals** - Menampilkan semua PO yang perlu diapprove
- **Purchase > My Approvals Dashboard** - Dashboard dengan view kanban yang lebih visual
- Menu ini hanya menampilkan PO yang sesuai dengan role user

#### **2. Dashboard Widget di Home Page**
- Widget akan muncul di home page jika ada PO yang perlu diapprove
- Menampilkan jumlah PO yang perlu diapprove berdasarkan level
- Link langsung ke approval dashboard

#### **3. Search dan Filter**
- **Purchase > Purchase Orders** → Filter "My Approvals"
- **Search berdasarkan approval level** (Manager, Department Head, CFO)
- **Filter berdasarkan state** (Manager Approval, Department Head Approval, CFO Approval)

#### **4. Notifikasi Visual**
- **Badge di menu** menunjukkan jumlah PO yang perlu diapprove
- **Color coding** di kanban view (biru=manager, kuning=dept head, hijau=CFO)
- **Status bar** menunjukkan progress approval

#### **5. Chatter/Log Note**
- Semua aktivitas approval tercatat di chatter
- Detail lengkap dengan nilai total dan threshold
- History approval yang bisa dilihat kapan saja

### **Workflow Notifikasi untuk Approver:**

#### **Untuk Manager:**
1. **Login ke Odoo**
2. **Buka Purchase > My Purchase Approvals**
3. **Lihat daftar PO** yang perlu diapprove (state: Manager Approval)
4. **Klik PO** untuk review detail
5. **Approve atau Reject** dengan alasan

#### **Untuk Department Head:**
1. **Login ke Odoo**
2. **Buka Purchase > My Purchase Approvals**
3. **Lihat daftar PO** yang perlu diapprove (state: Department Head Approval)
4. **Klik PO** untuk review detail
5. **Approve atau Reject** dengan alasan

#### **Untuk CFO:**
1. **Login ke Odoo**
2. **Buka Purchase > My Purchase Approvals**
3. **Lihat daftar PO** yang perlu diapprove (state: CFO Approval)
4. **Klik PO** untuk review detail
5. **Approve atau Reject** dengan alasan

### **Best Practices untuk Notifikasi Tanpa Email:**

#### **1. Regular Check**
- **Set jadwal regular** untuk cek menu My Purchase Approvals
- **Minimal 2x sehari** (pagi dan sore)
- **Prioritaskan PO dengan nilai tinggi**

#### **2. Dashboard Monitoring**
- **Gunakan My Approvals Dashboard** untuk overview visual
- **Monitor jumlah PO** yang pending approval
- **Track approval time** untuk performance

#### **3. Communication**
- **Informasikan ke team** tentang workflow approval
- **Set expectation** untuk response time
- **Buat SOP** untuk approval process

#### **4. Escalation**
- **Jika PO pending > 24 jam**, escalate ke level atas
- **Untuk PO urgent**, bisa langsung contact approver
- **Set reminder** untuk PO yang belum diapprove

### **Alternative Notifikasi:**

#### **1. Internal Chat/IM**
- **Slack, Teams, atau WhatsApp** untuk notifikasi urgent
- **Tag approver** di chat dengan link PO
- **Set reminder** otomatis

#### **2. Calendar Reminder**
- **Set calendar event** untuk review approval
- **Daily reminder** untuk cek My Purchase Approvals
- **Weekly review** untuk approval performance

#### **3. Report dan Analytics**
- **Daily report** PO yang pending approval
- **Weekly summary** approval performance
- **Monthly review** untuk improvement

### **Enable Email Kembali (Jika Perlu):**
```python
self.env['ir.config_parameter'].sudo().set_param('majid_purchase_approval.enable_email_notification', 'True')
```

## Field Baru

### Purchase Order Fields:
- `approval_level`: Level approval saat ini (manager/dept_head/cfo)
- `approval_threshold`: Threshold berdasarkan nilai (low/medium/high)
- `submitted_by`: User yang submit PO
- `submitted_date`: Tanggal submit
- `approved_by_*`: User yang approve di setiap level
- `approved_date_*`: Tanggal approval di setiap level
- `rejection_reason`: Alasan rejection
- `rejected_by`: User yang reject
- `rejected_date`: Tanggal rejection
- `my_approvals`: Computed field untuk filter PO yang perlu diapprove

### User Fields:
- `approval_role`: Role approval user (manager/dept_head/cfo)

## Workflow Detail

### Low Value (< 5M):
```
Draft → Manager Approval → Purchase Order
```

### Medium Value (5M-20M):
```
Draft → Department Head Approval → CFO Approval → Purchase Order
```

### High Value (> 20M):
```
Draft → CFO Approval → Purchase Order
```

## Email Templates

### 1. Approval Notification
- **Template ID**: `majid_purchase_approval.email_template_purchase_approval`
- **Recipient**: Approver email
- **Content**: Informasi PO yang perlu diapprove

### 2. Rejection Notification  
- **Template ID**: `majid_purchase_approval.email_template_purchase_rejection`
- **Recipient**: Submitter email
- **Content**: Alasan rejection

## Troubleshooting

### 1. User tidak bisa approve
- Pastikan user sudah di-assign ke group yang sesuai
- Cek field `approval_role` di user

### 2. Email tidak terkirim
- Pastikan email template sudah terinstall
- Cek konfigurasi email server
- Cek log error di Odoo

### 3. State tidak berubah
- Pastikan user memiliki permission yang tepat
- Cek log error di Odoo

### 4. Email Configuration Error
Jika muncul error "Unable to send message, please configure the sender's email address":

#### **Solusi 1: Konfigurasi SMTP Server**
1. Buka **Settings > Technical > Email > Outgoing Mail Servers**
2. Tambahkan SMTP server (Gmail, Outlook, dll)
3. Test koneksi

#### **Solusi 2: Disable Email Sementara**
Jalankan command ini di Odoo shell:
```python
self.env['ir.config_parameter'].sudo().set_param('majid_purchase_approval.enable_email_notification', 'False')
```

#### **Solusi 3: Cek User Email**
1. Buka **Settings > Users & Companies > Users**
2. Pastikan setiap user memiliki email yang valid

## Keunggulan State Baru

1. **Tracking Lebih Detail**: Setiap level approval memiliki state sendiri
2. **Filter Lebih Mudah**: Bisa filter berdasarkan state spesifik
3. **Workflow Lebih Jelas**: State menunjukkan posisi PO dalam approval flow
4. **Reporting Lebih Akurat**: Bisa report berdasarkan state approval
5. **User Experience Lebih Baik**: User tahu persis status PO

## Kompatibilitas

- Odoo 18.0+
- Modul Purchase (standar)
- Modul Mail (standar)

## Support

Untuk support dan pertanyaan, silakan hubungi developer. 