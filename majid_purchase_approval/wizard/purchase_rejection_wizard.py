from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRejectionWizard(models.TransientModel):
    _name = 'purchase.rejection.wizard'
    _description = 'Purchase Order Rejection Wizard'
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    rejected_by = fields.Many2one('res.users', string='Rejected By', default=lambda self: self.env.user)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    
    def action_reject(self):
        """Reject PO dengan alasan yang diberikan"""
        self.ensure_one()
        
        if not self.rejection_reason:
            raise UserError(_('Alasan rejection harus diisi'))
        
        # Reject PO
        self.purchase_order_id.reject_po(self.rejection_reason)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Purchase Order berhasil di-reject'),
                'type': 'success',
            }
        } 