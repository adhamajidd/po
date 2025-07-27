from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # Override state field untuk menambahkan state approval yang lebih spesifik
    state = fields.Selection(selection_add=[
        ('manager_approval', 'Manager Approval'),
        ('dept_head_approval', 'Department Head Approval'),
        ('cfo_approval', 'CFO Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], ondelete={
        'manager_approval': 'set default',
        'dept_head_approval': 'set default',
        'cfo_approval': 'set default',
        'approved': 'set default',
        'rejected': 'set default'
    })
    
    # Approval fields
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
    approval_threshold = fields.Selection([
        ('low', 'Low (< 5M)'),
        ('medium', 'Medium (5M-20M)'),
        ('high', 'High (> 20M)')
    ], string='Approval Threshold', compute='_compute_approval_threshold', store=True)
    
    # Search fields
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
    
    # Override button_confirm untuk custom approval flow
    def button_confirm(self):
        """Override button_confirm untuk custom approval flow"""
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            
            # Custom approval flow berdasarkan nilai total
            if order.amount_total < 5000000:
                # Low value - langsung ke Manager
                order._submit_for_manager_approval()
            elif order.amount_total <= 20000000:
                # Medium value - ke Department Head
                order._submit_for_dept_head_approval()
            else:
                # High value - langsung ke CFO
                order._submit_for_cfo_approval()
            
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        
        return True
    
    def _submit_for_manager_approval(self):
        """Submit untuk approval manager"""
        self.ensure_one()
        self.approval_level = 'manager'
        self.state = 'manager_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        self._send_approval_notification()
        
        # Log di chatter
        self.message_post(
            body=_('Purchase Order di-submit untuk approval Manager oleh %s') % self.env.user.name,
            subject=_('PO Submitted for Manager Approval')
        )
    
    def _submit_for_dept_head_approval(self):
        """Submit untuk approval department head"""
        self.ensure_one()
        self.approval_level = 'dept_head'
        self.state = 'dept_head_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        self._send_approval_notification()
        
        # Log di chatter
        self.message_post(
            body=_('Purchase Order di-submit untuk approval Department Head oleh %s') % self.env.user.name,
            subject=_('PO Submitted for Department Head Approval')
        )
    
    def _submit_for_cfo_approval(self):
        """Submit untuk approval CFO"""
        self.ensure_one()
        self.approval_level = 'cfo'
        self.state = 'cfo_approval'
        self.submitted_by = self.env.user
        self.submitted_date = fields.Datetime.now()
        self._send_approval_notification()
        
        # Log di chatter
        self.message_post(
            body=_('Purchase Order di-submit untuk approval CFO oleh %s') % self.env.user.name,
            subject=_('PO Submitted for CFO Approval')
        )
    
    # Override button_approve untuk custom approval flow
    def button_approve(self, force=False):
        """Override button_approve untuk custom approval flow"""
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
                    order.message_post(
                        body=_('Purchase Order di-approve oleh Manager %s') % self.env.user.name,
                        subject=_('PO Approved by Manager')
                    )
                else:
                    # Lanjut ke level berikutnya
                    next_level = approval_flow[1]  # dept_head
                    order.approval_level = next_level
                    order.state = 'dept_head_approval'
                    order._send_approval_notification()
                    order.message_post(
                        body=_('Purchase Order di-approve oleh Manager %s. Menunggu approval Department Head') % self.env.user.name,
                        subject=_('PO Approved by Manager - Waiting for Department Head')
                    )
                    
            elif current_level == 'dept_head':
                order.approved_by_dept_head = self.env.user
                order.approved_date_dept_head = fields.Datetime.now()
                # Lanjut ke CFO
                order.approval_level = 'cfo'
                order.state = 'cfo_approval'
                order._send_approval_notification()
                order.message_post(
                    body=_('Purchase Order di-approve oleh Department Head %s. Menunggu approval CFO') % self.env.user.name,
                    subject=_('PO Approved by Department Head - Waiting for CFO')
                )
                
            elif current_level == 'cfo':
                order.approved_by_cfo = self.env.user
                order.approved_date_cfo = fields.Datetime.now()
                # Final approval
                order.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
                order.approval_level = False
                order.message_post(
                    body=_('Purchase Order di-approve oleh CFO %s') % self.env.user.name,
                    subject=_('PO Approved by CFO')
                )
        
        return {}
    
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
        
        if not self.approval_level or self.state not in ['manager_approval', 'dept_head_approval', 'cfo_approval']:
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
    
    def reject_po(self, reason):
        """Reject PO dengan alasan"""
        self.ensure_one()
        
        self.state = 'rejected'
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
        if self.state not in ['draft', 'cancel', 'rejected']:
            self.state = 'draft'
            self.approval_level = False
            self.submitted_by = False
            self.submitted_date = False
            self.rejection_reason = False
            self.rejected_by = False
            self.rejected_date = False 