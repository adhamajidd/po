from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # Approval fields
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('manager_approved', 'Manager Approved'),
        ('dept_head_approved', 'Department Head Approved'),
        ('cfo_approved', 'CFO Approved'),
        ('rejected', 'Rejected'),
        ('approved', 'Fully Approved')
    ], string='Approval State', default='draft', tracking=True)
    
    approval_level = fields.Selection([
        ('manager', 'Manager'),
        ('dept_head', 'Department Head'),
        ('cfo', 'CFO')
    ], string='Current Approval Level', tracking=True)
    
    submitted_by = fields.Many2one('res.users', string='Submitted By', tracking=True)
    submitted_date = fields.Datetime(string='Submitted Date', tracking=True)
    
    approved_by_manager = fields.Many2one('res.users', string='Approved by Manager', tracking=True)
    approved_by_dept_head = fields.Many2one('res.users', string='Approved by Department Head', tracking=True)
    approved_by_cfo = fields.Many2one('res.users', string='Approved by CFO', tracking=True)
    
    approved_date_manager = fields.Datetime(string='Manager Approval Date', tracking=True)
    approved_date_dept_head = fields.Datetime(string='Department Head Approval Date', tracking=True)
    approved_date_cfo = fields.Datetime(string='CFO Approval Date', tracking=True)
    
    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    rejected_by = fields.Many2one('res.users', string='Rejected By', tracking=True)
    rejected_date = fields.Datetime(string='Rejection Date', tracking=True)
    
    # Computed fields
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True)
    approval_threshold = fields.Selection([
        ('low', 'Low (< 5M)'),
        ('medium', 'Medium (5M-20M)'),
        ('high', 'High (> 20M)')
    ], string='Approval Threshold', compute='_compute_approval_threshold', store=True)
    
    # Search fields
    my_approvals = fields.Boolean(string='My Approvals', compute='_compute_my_approvals', search='_search_my_approvals')
    
    @api.depends('amount_total')
    def _compute_total_amount(self):
        for po in self:
            po.total_amount = po.amount_total
    
    @api.depends('total_amount')
    def _compute_approval_threshold(self):
        for po in self:
            if po.total_amount < 5000000:
                po.approval_threshold = 'low'
            elif po.total_amount <= 20000000:
                po.approval_threshold = 'medium'
            else:
                po.approval_threshold = 'high'
    
    @api.depends('approval_level', 'approval_state')
    def _compute_my_approvals(self):
        """Compute field untuk mengecek apakah PO perlu diapprove oleh user saat ini"""
        for po in self:
            po.my_approvals = po._can_approve()
    
    def _get_approval_flow(self):
        """Menentukan flow approval berdasarkan nilai total"""
        self.ensure_one()
        if self.approval_threshold == 'low':
            return ['manager']
        elif self.approval_threshold == 'medium':
            return ['dept_head', 'cfo']
        else:  # high
            return ['cfo']
    
    def _get_approver_for_level(self, level):
        """Mendapatkan approver untuk level tertentu"""
        self.ensure_one()
        
        if level == 'manager':
            # Cari user dengan role Manager
            manager_group = self.env.ref('majid_purchase_approval.group_purchase_manager')
            return self.env['res.users'].search([('groups_id', 'in', manager_group.id)], limit=1)
        
        elif level == 'dept_head':
            # Cari user dengan role Department Head
            dept_head_group = self.env.ref('majid_purchase_approval.group_purchase_dept_head')
            return self.env['res.users'].search([('groups_id', 'in', dept_head_group.id)], limit=1)
        
        elif level == 'cfo':
            # Cari user dengan role CFO
            cfo_group = self.env.ref('majid_purchase_approval.group_purchase_cfo')
            return self.env['res.users'].search([('groups_id', 'in', cfo_group.id)], limit=1)
        
        return False
    
    def action_submit_for_approval(self):
        """Submit PO untuk approval"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_('Hanya PO dengan status Draft yang dapat di-submit untuk approval'))
        
        if self.approval_state not in ['draft', 'rejected']:
            raise UserError(_('PO sudah di-submit untuk approval'))
        
        # Reset approval fields jika sebelumnya di-reject
        if self.approval_state == 'rejected':
            self.rejection_reason = False
            self.rejected_by = False
            self.rejected_date = False
        
        # Set approval level pertama
        approval_flow = self._get_approval_flow()
        if not approval_flow:
            raise UserError(_('Tidak dapat menentukan flow approval'))
        
        self.approval_level = approval_flow[0]
        self.approval_state = 'submitted'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        
        # Kirim email notification
        self._send_approval_notification()
        
        # Log di chatter
        self.message_post(
            body=_('Purchase Order di-submit untuk approval oleh %s') % self.env.user.name,
            subject=_('PO Submitted for Approval')
        )
        
        return True
    
    def action_approve(self):
        """Approve PO pada level saat ini"""
        self.ensure_one()
        
        if not self._can_approve():
            raise AccessError(_('Anda tidak memiliki hak untuk approve PO ini'))
        
        current_level = self.approval_level
        approval_flow = self._get_approval_flow()
        
        # Update approval info
        if current_level == 'manager':
            self.approved_by_manager = self.env.user
            self.approved_date_manager = fields.Datetime.now()
            self.approval_state = 'manager_approved'
        elif current_level == 'dept_head':
            self.approved_by_dept_head = self.env.user
            self.approved_date_dept_head = fields.Datetime.now()
            self.approval_state = 'dept_head_approved'
        elif current_level == 'cfo':
            self.approved_by_cfo = self.env.user
            self.approved_date_cfo = fields.Datetime.now()
            self.approval_state = 'cfo_approved'
        
        # Cek apakah ada level approval berikutnya
        current_index = approval_flow.index(current_level)
        if current_index + 1 < len(approval_flow):
            # Masih ada level approval berikutnya
            next_level = approval_flow[current_index + 1]
            self.approval_level = next_level
            
            # Kirim email notification untuk level berikutnya
            self._send_approval_notification()
            
            # Log di chatter
            self.message_post(
                body=_('Purchase Order di-approve oleh %s. Menunggu approval dari %s') % 
                     (self.env.user.name, next_level.replace('_', ' ').title()),
                subject=_('PO Approved - Waiting for Next Level')
            )
        else:
            # Approval selesai
            self.approval_state = 'approved'
            self.approval_level = False
            
            # Log di chatter
            self.message_post(
                body=_('Purchase Order telah di-approve sepenuhnya oleh %s') % self.env.user.name,
                subject=_('PO Fully Approved')
            )
        
        return True
    
    def action_reject(self):
        """Reject PO"""
        self.ensure_one()
        
        if not self._can_approve():
            raise AccessError(_('Anda tidak memiliki hak untuk reject PO ini'))
        
        # Buka wizard untuk input alasan rejection
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
    
    def _can_approve(self):
        """Cek apakah user saat ini dapat approve/reject PO"""
        self.ensure_one()
        
        if not self.approval_level:
            return False
        
        current_level = self.approval_level
        
        if current_level == 'manager':
            return self.env.user.has_group('majid_purchase_approval.group_purchase_manager')
        elif current_level == 'dept_head':
            return self.env.user.has_group('majid_purchase_approval.group_purchase_dept_head')
        elif current_level == 'cfo':
            return self.env.user.has_group('majid_purchase_approval.group_purchase_cfo')
        
        return False
    
    def _send_approval_notification(self):
        """Kirim email notification untuk approval"""
        self.ensure_one()
        
        if not self.approval_level:
            return
        
        approver = self._get_approver_for_level(self.approval_level)
        if not approver:
            _logger.warning('Tidak dapat menemukan approver untuk level %s', self.approval_level)
            return
        
        # Template email
        template = self.env.ref('majid_purchase_approval.email_template_purchase_approval')
        if template and approver.email:
            template.with_context(
                approval_level=self.approval_level,
                approver_email=approver.email,
                purchase_order=self
            ).send_mail(self.id, force_send=True)
    
    def _send_rejection_notification(self, reason):
        """Kirim email notification untuk rejection"""
        self.ensure_one()
        
        # Template email rejection
        template = self.env.ref('majid_purchase_approval.email_template_purchase_rejection')
        if template and self.submitted_by.email:
            template.with_context(
                rejection_reason=reason,
                purchase_order=self
            ).send_mail(self.id, force_send=True)
    
    @api.model
    def _get_approval_domain(self):
        """Domain untuk PO yang perlu diapprove oleh user saat ini"""
        user = self.env.user
        
        if user.has_group('majid_purchase_approval.group_purchase_manager'):
            return [('approval_level', '=', 'manager'), ('approval_state', '=', 'submitted')]
        elif user.has_group('majid_purchase_approval.group_purchase_dept_head'):
            return [('approval_level', '=', 'dept_head'), ('approval_state', 'in', ['submitted', 'manager_approved'])]
        elif user.has_group('majid_purchase_approval.group_purchase_cfo'):
            return [('approval_level', '=', 'cfo'), ('approval_state', 'in', ['submitted', 'manager_approved', 'dept_head_approved'])]
        
        return [('id', '=', False)]  # Empty domain
    
    @api.model
    def _search_my_approvals(self, operator, value):
        """Search method untuk filter My Approvals"""
        domain = self._get_approval_domain()
        return domain
    
    def reject_po(self, reason):
        """Reject PO dengan alasan"""
        self.ensure_one()
        
        self.approval_state = 'rejected'
        self.rejection_reason = reason
        self.rejected_by = self.env.user
        self.rejected_date = fields.Datetime.now()
        self.approval_level = False
        
        # Kirim email notification
        self._send_rejection_notification(reason)
        
        # Log di chatter
        self.message_post(
            body=_('Purchase Order di-reject oleh %s. Alasan: %s') % (self.env.user.name, reason),
            subject=_('PO Rejected')
        )
        
        return True
    
    @api.onchange('order_line')
    def _onchange_order_line(self):
        """Reset approval state ketika order line berubah"""
        super()._onchange_order_line()
        if self.approval_state not in ['draft', 'rejected']:
            self.approval_state = 'draft'
            self.approval_level = False
            self.submitted_by = False
            self.submitted_date = False
            self.rejection_reason = False
            self.rejected_by = False
            self.rejected_date = False 