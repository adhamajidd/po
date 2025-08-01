from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_amount
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Override state field untuk menambahkan state approval yang lebih spesifik
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('manager_approval', 'Manager'),
        ('dept_head_approval', 'Department Head'),
        ('cfo_approval', 'CFO'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected')
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    
    # Approval fields
    approval_level = fields.Selection([
        ('manager', 'Manager'),
        ('dept_head', 'Department Head'),
        ('cfo', 'CFO')
    ], string='Approval Level', tracking=True)
    
    approval_threshold = fields.Selection([
        ('low', 'Low (< 5M)'),
        ('medium', 'Medium (5M-20M)'),
        ('high', 'High (> 20M)')
    ], string='Approval Threshold', compute='_compute_approval_threshold', store=True)
    
    # User tracking
    submitted_by = fields.Many2one('res.users', string='Submitted By', tracking=True)
    submitted_date = fields.Datetime(string='Submitted Date', tracking=True)
    
    # Approval tracking
    approved_by_manager = fields.Many2one('res.users', string='Approved by Manager', tracking=True)
    approved_by_dept_head = fields.Many2one('res.users', string='Approved by Department Head', tracking=True)
    approved_by_cfo = fields.Many2one('res.users', string='Approved by CFO', tracking=True)
    
    approved_date_manager = fields.Datetime(string='Manager Approval Date', tracking=True)
    approved_date_dept_head = fields.Datetime(string='Department Head Approval Date', tracking=True)
    approved_date_cfo = fields.Datetime(string='CFO Approval Date', tracking=True)
    
    # Rejection tracking
    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    rejected_by = fields.Many2one('res.users', string='Rejected By', tracking=True)
    rejected_date = fields.Datetime(string='Rejection Date', tracking=True)
    
    # Computed fields
    my_approvals = fields.Boolean(string='My Approvals', compute='_compute_my_approvals', search='_search_my_approvals')
    
    @api.depends('amount_total')
    def _compute_approval_threshold(self):
        for po in self:
            if po.amount_total < 5000000:
                po.approval_threshold = 'low'
            elif po.amount_total <= 20000000:
                po.approval_threshold = 'medium'
            else:
                po.approval_threshold = 'high'
    
    @api.depends('approval_level', 'state')
    def _compute_my_approvals(self):
        """Compute field untuk mengecek apakah PO perlu diapprove oleh user saat ini"""
        for po in self:
            po.my_approvals = po._can_approve()
    
    def _can_approve(self):
        """Cek apakah user saat ini bisa approve PO ini"""
        self.ensure_one()
        user = self.env.user
        
        if user.has_group('majid_purchase_approval.group_purchase_manager'):
            return self.approval_level == 'manager' and self.state == 'manager_approval'
        elif user.has_group('majid_purchase_approval.group_purchase_dept_head'):
            return self.approval_level == 'dept_head' and self.state == 'dept_head_approval'
        elif user.has_group('majid_purchase_approval.group_purchase_cfo'):
            return self.approval_level == 'cfo' and self.state == 'cfo_approval'
        
        return False
    
    # Override button_confirm untuk custom approval flow
    def button_confirm(self):
        """Override button_confirm untuk custom approval flow"""
        self = self.filtered(lambda order: order._approval_allowed())
        
        for order in self:
            current_level = order.approval_level
            approval_flow = order._get_approval_flow()
            
            # Update approval info
            if current_level == 'manager':
                order.approved_by_manager = self.env.user
                order.approved_date_manager = fields.Datetime.now()
                # Jika hanya perlu approval manager, langsung approve
                if len(approval_flow) == 1:
                    order.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
                    order.approval_level = False
                    order._log_approval_activity('approve', self.env.user, 'Final approval - PO menjadi Purchase Order')
                else:
                    # Lanjut ke level berikutnya
                    next_level = approval_flow[1]  # dept_head
                    order.approval_level = next_level
                    order.state = 'dept_head_approval'
                    order._log_approval_activity('approve', self.env.user, 'Menunggu approval Department Head')
                    order._send_approval_notification()
                    
            elif current_level == 'dept_head':
                order.approved_by_dept_head = self.env.user
                order.approved_date_dept_head = fields.Datetime.now()
                # Lanjut ke CFO
                order.approval_level = 'cfo'
                order.state = 'cfo_approval'
                order._log_approval_activity('approve', self.env.user, 'Menunggu approval CFO')
                order._send_approval_notification()
                
            elif current_level == 'cfo':
                order.approved_by_cfo = self.env.user
                order.approved_date_cfo = fields.Datetime.now()
                # Final approval
                order.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
                order.approval_level = False
                order._log_approval_activity('approve', self.env.user, 'Final approval - PO menjadi Purchase Order')
        
        return {}
    
    def action_submit_for_approval(self):
        """Button Submit for Approval - terpisah dari Confirm Order"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_('Hanya Purchase Order dalam status Draft yang dapat di-submit untuk approval'))
        
        if not self.order_line:
            raise UserError(_('Purchase Order harus memiliki order line sebelum di-submit untuk approval'))
        
        # Tentukan approval flow berdasarkan nilai total
        approval_flow = self._get_approval_flow()
        
        if not approval_flow:
            raise UserError(_('Tidak dapat menentukan approval flow untuk nilai total ini'))
        
        # Set approval level pertama
        first_level = approval_flow[0]
        self.approval_level = first_level
        
        # Set state sesuai level pertama
        if first_level == 'manager':
            self._submit_for_manager_approval()
        elif first_level == 'dept_head':
            self._submit_for_dept_head_approval()
        elif first_level == 'cfo':
            self._submit_for_cfo_approval()
        
        # Return action untuk refresh halaman
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
        }
    
    def _submit_for_manager_approval(self):
        """Submit untuk approval manager"""
        self.ensure_one()
        self.approval_level = 'manager'
        self.state = 'manager_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        
        # Log aktivitas
        self._log_approval_activity('submit', self.env.user, 
                                    'Nilai total: %s, Threshold: %s' % (
                                        self.currency_id.symbol + ' ' + str(self.amount_total),
                                        self.approval_threshold
                                    ))
        
        # Kirim email notification
        self._send_approval_notification()
        
        # Log di chatter bahwa email sudah terkirim
        approver = self._get_approver_for_level('manager')
        if approver and approver.email:
            self.message_post(
                body=_('✅ Email notification berhasil dikirim ke %s (%s)') % (approver.name, approver.email),
                subject=_('Email Notification Sent'),
                message_type='notification'
            )
    
    def _submit_for_dept_head_approval(self):
        """Submit untuk approval department head"""
        self.ensure_one()
        self.approval_level = 'dept_head'
        self.state = 'dept_head_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        
        # Log aktivitas
        self._log_approval_activity('submit', self.env.user, 
                                    'Nilai total: %s, Threshold: %s' % (
                                        self.currency_id.symbol + ' ' + str(self.amount_total),
                                        self.approval_threshold
                                    ))
        
        # Kirim email notification
        self._send_approval_notification()
        
        # Log di chatter bahwa email sudah terkirim
        approver = self._get_approver_for_level('dept_head')
        if approver and approver.email:
            self.message_post(
                body=_('✅ Email notification berhasil dikirim ke %s (%s)') % (approver.name, approver.email),
                subject=_('Email Notification Sent'),
                message_type='notification'
            )
    
    def _submit_for_cfo_approval(self):
        """Submit untuk approval CFO"""
        self.ensure_one()
        self.approval_level = 'cfo'
        self.state = 'cfo_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        
        # Log aktivitas
        self._log_approval_activity('submit', self.env.user, 
                                    'Nilai total: %s, Threshold: %s' % (
                                        self.currency_id.symbol + ' ' + str(self.amount_total),
                                        self.approval_threshold
                                    ))
        
        # Kirim email notification
        self._send_approval_notification()
        
        # Log di chatter bahwa email sudah terkirim
        approver = self._get_approver_for_level('cfo')
        if approver and approver.email:
            self.message_post(
                body=_('✅ Email notification berhasil dikirim ke %s (%s)') % (approver.name, approver.email),
                subject=_('Email Notification Sent'),
                message_type='notification'
            )
    
    # Custom approval flow method
    def action_approve(self, force=False):
        """Custom approval flow method"""
        self = self.filtered(lambda order: order._approval_allowed())
        
        for order in self:
            current_level = order.approval_level
            approval_flow = order._get_approval_flow()
            
            # Update approval info
            if current_level == 'manager':
                order.approved_by_manager = self.env.user
                order.approved_date_manager = fields.Datetime.now()
                # Jika hanya perlu approval manager, langsung approve
                if len(approval_flow) == 1:
                    order.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
                    order.approval_level = False
                    order._log_approval_activity('approve', self.env.user, 'Final approval - PO menjadi Purchase Order')
                else:
                    # Lanjut ke level berikutnya
                    next_level = approval_flow[1]  # dept_head
                    order.approval_level = next_level
                    order.state = 'dept_head_approval'
                    order._log_approval_activity('approve', self.env.user, 'Menunggu approval Department Head')
                    order._send_approval_notification()
                    
            elif current_level == 'dept_head':
                order.approved_by_dept_head = self.env.user
                order.approved_date_dept_head = fields.Datetime.now()
                # Lanjut ke CFO
                order.approval_level = 'cfo'
                order.state = 'cfo_approval'
                order._log_approval_activity('approve', self.env.user, 'Menunggu approval CFO')
                order._send_approval_notification()
                
            elif current_level == 'cfo':
                order.approved_by_cfo = self.env.user
                order.approved_date_cfo = fields.Datetime.now()
                # Final approval
                order.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
                order.approval_level = False
                order._log_approval_activity('approve', self.env.user, 'Final approval - PO menjadi Purchase Order')
        
        # Return action untuk refresh halaman
        if len(self) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
                'flags': {'initial_mode': 'edit'},
            }
        
        return {}
    
    def action_reject(self):
        """Membuka wizard untuk alasan rejection"""
        self.ensure_one()
        
        if not self._can_approve():
            raise UserError(_('Anda tidak memiliki hak untuk reject Purchase Order ini'))
        
        return {
            'name': _('Reject Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_rejected_by': self.env.user.id,
            }
        }
    
    def _get_approval_flow(self):
        """Mendapatkan flow approval berdasarkan threshold"""
        self.ensure_one()
        
        if self.approval_threshold == 'low':
            return ['manager']
        elif self.approval_threshold == 'medium':
            return ['dept_head', 'cfo']
        elif self.approval_threshold == 'high':
            return ['cfo']
        
        return []
    
    def _get_approver_for_level(self, level):
        """Mendapatkan user approver untuk level tertentu"""
        self.ensure_one()
        
        if level == 'manager':
            return self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('majid_purchase_approval.group_purchase_manager').id)
            ], limit=1)
        elif level == 'dept_head':
            return self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('majid_purchase_approval.group_purchase_dept_head').id)
            ], limit=1)
        elif level == 'cfo':
            return self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('majid_purchase_approval.group_purchase_cfo').id)
            ], limit=1)
        
        return False
    
    def _send_approval_notification(self):
        """Kirim email notification untuk approval"""
        self.ensure_one()
        
        if not self.approval_level:
            return
        
        approver = self._get_approver_for_level(self.approval_level)
        if not approver or not approver.email:
            _logger.warning('Tidak dapat menemukan approver dengan email untuk level %s', self.approval_level)
            return
        
        # Template email
        template = self.env.ref('majid_purchase_approval.email_template_purchase_approval')
        if template:
            try:
                # Buat context yang lebih lengkap
                context = {
                    'approval_level': self.approval_level,
                    'approver_email': approver.email,
                    'purchase_order': self,
                    'lang': approver.lang or 'en_US',
                }
                
                template.with_context(**context).send_mail(self.id, force_send=True)
                _logger.info('Email approval notification berhasil dikirim ke %s', approver.email)
                
                # Log di chatter bahwa email berhasil dikirim
                self.message_post(
                    body=_('📧 Email approval notification berhasil dikirim ke %s (%s)') % (approver.name, approver.email),
                    subject=_('Email Sent Successfully'),
                    message_type='notification'
                )
                
            except Exception as e:
                _logger.error('Gagal mengirim email approval notification: %s', str(e))
                # Log error di chatter
                self.message_post(
                    body=_('❌ Gagal mengirim email approval notification: %s') % str(e),
                    subject=_('Email Send Failed'),
                    message_type='notification'
                )
                # Jangan crash aplikasi jika email gagal dikirim
                pass
    
    def _send_rejection_notification(self, reason):
        """Kirim email notification untuk rejection"""
        self.ensure_one()
        
        if not self.submitted_by or not self.submitted_by.email:
            _logger.warning('Tidak dapat menemukan email submitter untuk rejection notification')
            return
        
        # Template email rejection
        template = self.env.ref('majid_purchase_approval.email_template_purchase_rejection')
        if template:
            try:
                # Buat context yang lebih lengkap
                context = {
                    'rejection_reason': reason,
                    'purchase_order': self,
                    'lang': self.submitted_by.lang or 'en_US',
                }
                
                template.with_context(**context).send_mail(self.id, force_send=True)
                _logger.info('Email rejection notification berhasil dikirim ke %s', self.submitted_by.email)
                
                # Log di chatter bahwa email berhasil dikirim
                self.message_post(
                    body=_('📧 Email rejection notification berhasil dikirim ke %s (%s)') % (self.submitted_by.name, self.submitted_by.email),
                    subject=_('Rejection Email Sent'),
                    message_type='notification'
                )
                
            except Exception as e:
                _logger.error('Gagal mengirim email rejection notification: %s', str(e))
                # Log error di chatter
                self.message_post(
                    body=_('❌ Gagal mengirim email rejection notification: %s') % str(e),
                    subject=_('Rejection Email Failed'),
                    message_type='notification'
                )
                # Jangan crash aplikasi jika email gagal dikirim
                pass
    
    @api.model
    def _get_approval_domain(self):
        """Domain untuk PO yang perlu diapprove oleh user saat ini"""
        user = self.env.user
        
        if user.has_group('majid_purchase_approval.group_purchase_manager'):
            return [('approval_level', '=', 'manager'), ('state', '=', 'manager_approval')]
        elif user.has_group('majid_purchase_approval.group_purchase_dept_head'):
            return [('approval_level', '=', 'dept_head'), ('state', '=', 'dept_head_approval')]
        elif user.has_group('majid_purchase_approval.group_purchase_cfo'):
            return [('approval_level', '=', 'cfo'), ('state', '=', 'cfo_approval')]
        
        return [('id', '=', False)]  # Empty domain
    
    @api.model
    def _search_my_approvals(self, operator, value):
        """Search method untuk filter My Approvals"""
        domain = self._get_approval_domain()
        return domain
    
    @api.model
    def get_my_approval_count(self):
        """Mendapatkan jumlah PO yang perlu diapprove oleh user saat ini"""
        domain = self._get_approval_domain()
        return self.search_count(domain)
    
    @api.model
    def get_approval_summary(self):
        """Mendapatkan summary approval untuk dashboard"""
        user = self.env.user
        
        # Count berdasarkan level approval
        manager_count = 0
        dept_head_count = 0
        cfo_count = 0
        
        if user.has_group('majid_purchase_approval.group_purchase_manager'):
            manager_count = self.search_count([
                ('approval_level', '=', 'manager'), 
                ('state', '=', 'manager_approval')
            ])
        
        if user.has_group('majid_purchase_approval.group_purchase_dept_head'):
            dept_head_count = self.search_count([
                ('approval_level', '=', 'dept_head'), 
                ('state', '=', 'dept_head_approval')
            ])
        
        if user.has_group('majid_purchase_approval.group_purchase_cfo'):
            cfo_count = self.search_count([
                ('approval_level', '=', 'cfo'), 
                ('state', '=', 'cfo_approval')
            ])
        
        total_count = manager_count + dept_head_count + cfo_count
        
        return {
            'total_count': total_count,
            'manager_count': manager_count,
            'dept_head_count': dept_head_count,
            'cfo_count': cfo_count,
            'has_approvals': total_count > 0
        }
    
    def reject_po(self, reason):
        """Reject PO dengan alasan"""
        self.ensure_one()
        
        if not self.approval_level or self.state not in ['manager_approval', 'dept_head_approval', 'cfo_approval']:
            return False
        
        self.rejection_reason = reason
        self.rejected_by = self.env.user
        self.rejected_date = fields.Datetime.now()
        self.approval_level = False
        self.state = 'rejected'
        
        # Log aktivitas rejection
        self._log_approval_activity('reject', self.env.user, reason)
        
        # Kirim email notification rejection
        self._send_rejection_notification(reason)
        
        return True
    
    def _log_approval_activity(self, action, user, details=""):
        """Log aktivitas approval di chatter"""
        self.ensure_one()
        
        # Buat log message yang informatif
        if action == 'submit':
            approval_level_display = self.approval_level.replace('_', ' ').title() if self.approval_level else 'Unknown'
            message = _('Purchase Order di-submit untuk approval %s oleh %s. %s') % (
                approval_level_display, 
                user.name, 
                details
            )
            subject = _('PO Submitted for %s Approval') % approval_level_display
            
        elif action == 'approve':
            approval_level_display = self.approval_level.replace('_', ' ').title() if self.approval_level else 'Unknown'
            message = _('Purchase Order di-approve oleh %s (%s). %s') % (
                user.name, 
                approval_level_display,
                details
            )
            subject = _('PO Approved by %s') % approval_level_display
            
        elif action == 'reject':
            # Untuk rejection, approval_level sudah diset ke False, jadi gunakan info dari user
            user_role = 'Unknown'
            if user.has_group('majid_purchase_approval.group_purchase_manager'):
                user_role = 'Manager'
            elif user.has_group('majid_purchase_approval.group_purchase_dept_head'):
                user_role = 'Department Head'
            elif user.has_group('majid_purchase_approval.group_purchase_cfo'):
                user_role = 'CFO'
            
            message = _('Purchase Order di-reject oleh %s (%s). Alasan: %s') % (
                user.name, 
                user_role,
                details
            )
            subject = _('PO Rejected by %s') % user_role
            
        else:
            message = _('Aktivitas approval: %s oleh %s. %s') % (action, user.name, details)
            subject = _('PO Approval Activity')
        
        # Post message ke chatter
        self.message_post(
            body=message,
            subject=subject,
            message_type='notification'
        )
        
        _logger.info('Log approval activity: %s', message)
    
    @api.onchange('order_line')
    def _onchange_order_line(self):
        """Reset approval state ketika order line berubah"""
        if self.state not in ['draft', 'cancel', 'rejected']:
            self.state = 'draft'
            self.approval_level = False
            self.submitted_by = False
            self.submitted_date = False
            self.rejection_reason = False
            self.rejected_by = False
            self.rejected_date = False 