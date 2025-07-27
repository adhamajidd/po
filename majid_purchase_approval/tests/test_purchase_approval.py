from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, AccessError

class TestPurchaseApproval(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Create test users
        self.manager_user = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test.manager',
            'email': 'test.manager@test.com',
            'approval_role': 'manager',
        })
        
        self.dept_head_user = self.env['res.users'].create({
            'name': 'Test Department Head',
            'login': 'test.depthead',
            'email': 'test.depthead@test.com',
            'approval_role': 'dept_head',
        })
        
        self.cfo_user = self.env['res.users'].create({
            'name': 'Test CFO',
            'login': 'test.cfo',
            'email': 'test.cfo@test.com',
            'approval_role': 'cfo',
        })
        
        # Create test vendor
        self.vendor = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })
        
        # Create test products
        self.product_low = self.env['product.product'].create({
            'name': 'Test Product Low',
            'type': 'product',
            'list_price': 1000000,
        })
        
        self.product_medium = self.env['product.product'].create({
            'name': 'Test Product Medium',
            'type': 'product',
            'list_price': 10000000,
        })
        
        self.product_high = self.env['product.product'].create({
            'name': 'Test Product High',
            'type': 'product',
            'list_price': 25000000,
        })
    
    def test_approval_threshold_low(self):
        """Test approval threshold untuk nilai rendah"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_low.id,
                'name': self.product_low.name,
                'product_qty': 1,
                'product_uom': self.product_low.uom_id.id,
                'price_unit': 1000000,
            })]
        })
        
        self.assertEqual(po.approval_threshold, 'low')
        self.assertEqual(po._get_approval_flow(), ['manager'])
    
    def test_approval_threshold_medium(self):
        """Test approval threshold untuk nilai menengah"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_medium.id,
                'name': self.product_medium.name,
                'product_qty': 1,
                'product_uom': self.product_medium.uom_id.id,
                'price_unit': 10000000,
            })]
        })
        
        self.assertEqual(po.approval_threshold, 'medium')
        self.assertEqual(po._get_approval_flow(), ['dept_head', 'cfo'])
    
    def test_approval_threshold_high(self):
        """Test approval threshold untuk nilai tinggi"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_high.id,
                'name': self.product_high.name,
                'product_qty': 1,
                'product_uom': self.product_high.uom_id.id,
                'price_unit': 25000000,
            })]
        })
        
        self.assertEqual(po.approval_threshold, 'high')
        self.assertEqual(po._get_approval_flow(), ['cfo'])
    
    def test_submit_for_approval_low(self):
        """Test submit untuk approval nilai rendah"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_low.id,
                'name': self.product_low.name,
                'product_qty': 1,
                'product_uom': self.product_low.uom_id.id,
                'price_unit': 1000000,
            })]
        })
        
        # Submit untuk approval
        po.action_submit_for_approval()
        
        self.assertEqual(po.approval_state, 'submitted')
        self.assertEqual(po.approval_level, 'manager')
        self.assertEqual(po.submitted_by, self.env.user)
    
    def test_approve_by_manager(self):
        """Test approve oleh manager"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_low.id,
                'name': self.product_low.name,
                'product_qty': 1,
                'product_uom': self.product_low.uom_id.id,
                'price_unit': 1000000,
            })]
        })
        
        # Submit untuk approval
        po.action_submit_for_approval()
        
        # Switch ke user manager
        po.with_user(self.manager_user).action_approve()
        
        self.assertEqual(po.approval_state, 'approved')
        self.assertEqual(po.approved_by_manager, self.manager_user)
    
    def test_reject_po(self):
        """Test reject PO"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_low.id,
                'name': self.product_low.name,
                'product_qty': 1,
                'product_uom': self.product_low.uom_id.id,
                'price_unit': 1000000,
            })]
        })
        
        # Submit untuk approval
        po.action_submit_for_approval()
        
        # Reject PO
        po.with_user(self.manager_user).reject_po('Test rejection reason')
        
        self.assertEqual(po.approval_state, 'rejected')
        self.assertEqual(po.rejection_reason, 'Test rejection reason')
        self.assertEqual(po.rejected_by, self.manager_user)
    
    def test_medium_approval_flow(self):
        """Test approval flow untuk nilai menengah"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_medium.id,
                'name': self.product_medium.name,
                'product_qty': 1,
                'product_uom': self.product_medium.uom_id.id,
                'price_unit': 10000000,
            })]
        })
        
        # Submit untuk approval
        po.action_submit_for_approval()
        self.assertEqual(po.approval_level, 'dept_head')
        
        # Approve oleh department head
        po.with_user(self.dept_head_user).action_approve()
        self.assertEqual(po.approval_state, 'dept_head_approved')
        self.assertEqual(po.approval_level, 'cfo')
        
        # Approve oleh CFO
        po.with_user(self.cfo_user).action_approve()
        self.assertEqual(po.approval_state, 'approved')
        self.assertEqual(po.approval_level, False)
    
    def test_access_control(self):
        """Test access control untuk approval"""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_low.id,
                'name': self.product_low.name,
                'product_qty': 1,
                'product_uom': self.product_low.uom_id.id,
                'price_unit': 1000000,
            })]
        })
        
        # Submit untuk approval
        po.action_submit_for_approval()
        
        # Test bahwa user tanpa role tidak bisa approve
        with self.assertRaises(AccessError):
            po.with_user(self.env.user).action_approve()
        
        # Test bahwa manager bisa approve
        po.with_user(self.manager_user).action_approve()
        self.assertEqual(po.approval_state, 'approved') 