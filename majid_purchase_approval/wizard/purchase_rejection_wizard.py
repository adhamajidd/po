from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRejectionWizard(models.TransientModel):
    _name = 'purchase.rejection.wizard'
    _description = 'Purchase Order Rejection Wizard'
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    rejected_by = fields.Many2one('res.users', string='Rejected By', default=lambda self: self.env.user)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    
    def action_reject(self):
        """Action untuk reject PO dengan alasan"""
        self.ensure_one()
        
        if not self.rejection_reason:
            raise UserError(_('Alasan rejection harus diisi'))
        
        # Reject PO
        self.purchase_order_id.reject_po(self.rejection_reason)
        
        # Return action untuk refresh halaman PO
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
        } 