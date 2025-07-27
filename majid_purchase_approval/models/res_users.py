from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    approval_role = fields.Selection([
        ('none', 'None'),
        ('manager', 'Purchase Manager'),
        ('dept_head', 'Department Head'),
        ('cfo', 'CFO')
    ], string='Approval Role', default='none')
    
    @api.onchange('approval_role')
    def _onchange_approval_role(self):
        """Update group membership berdasarkan approval role"""
        if not self.approval_role or self.approval_role == 'none':
            return
        
        # Hapus semua group approval sebelumnya
        manager_group = self.env.ref('majid_purchase_approval.group_purchase_manager', raise_if_not_found=False)
        dept_head_group = self.env.ref('majid_purchase_approval.group_purchase_dept_head', raise_if_not_found=False)
        cfo_group = self.env.ref('majid_purchase_approval.group_purchase_cfo', raise_if_not_found=False)
        
        if manager_group:
            self.groups_id = [(3, manager_group.id)]
        if dept_head_group:
            self.groups_id = [(3, dept_head_group.id)]
        if cfo_group:
            self.groups_id = [(3, cfo_group.id)]
        
        # Tambahkan group sesuai role
        if self.approval_role == 'manager' and manager_group:
            self.groups_id = [(4, manager_group.id)]
        elif self.approval_role == 'dept_head' and dept_head_group:
            self.groups_id = [(4, dept_head_group.id)]
        elif self.approval_role == 'cfo' and cfo_group:
            self.groups_id = [(4, cfo_group.id)] 