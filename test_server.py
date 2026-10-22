"""
=============================================================================
 FarmDirect - Automated Test Suite
 Tests all backend routes, role authentications, cart, checkout & database
=============================================================================
Run using:
    python test_server.py
"""

import unittest
import json
import os
from server import app, USERS_FILE, PRODUCTS_FILE, ORDERS_FILE, MESSAGES_FILE, read_json, write_json

class FarmDirectTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test client and create backup copies of JSON data."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Backup original JSON databases so tests do not pollute data
        self.users_backup = read_json(USERS_FILE)
        self.products_backup = read_json(PRODUCTS_FILE)
        self.orders_backup = read_json(ORDERS_FILE)
        self.messages_backup = read_json(MESSAGES_FILE)

    def tearDown(self):
        """Restore original JSON data after each test."""
        write_json(USERS_FILE, self.users_backup)
        write_json(PRODUCTS_FILE, self.products_backup)
        write_json(ORDERS_FILE, self.orders_backup)
        write_json(MESSAGES_FILE, self.messages_backup)

    # -------------------------------------------------------------------------
    # 1. Public Pages Tests
    # -------------------------------------------------------------------------
    def test_home_page(self):
        """Test home page loads with 200 OK and contains FarmDirect branding."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FarmDirect", response.data)
        self.assertIn(b"Featured Fresh Harvest", response.data)

    def test_marketplace_page(self):
        """Test marketplace catalog loads and displays items."""
        response = self.client.get('/marketplace')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Farm Marketplace", response.data)

    def test_marketplace_filter_search(self):
        """Test search filter query."""
        response = self.client.get('/marketplace?q=tomatoes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tomatoes", response.data)

    def test_marketplace_filter_category(self):
        """Test category filter."""
        response = self.client.get('/marketplace?category=Fruits')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Apples", response.data)

    def test_product_detail_page(self):
        """Test individual product detail page."""
        response = self.client.get('/product/prod-1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tomatoes", response.data)
        self.assertIn(b"Green Earth Organic Farm", response.data)

    def test_about_page(self):
        """Test about us page."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"The Middlemen-Free Agriculture Movement", response.data)

    def test_contact_submission(self):
        """Test submitting the contact form."""
        response = self.client.post('/contact', data={
            'name': 'Test User',
            'email': 'testuser@example.com',
            'subject': 'Testing Contact Form',
            'message': 'This is a test automated inquiry.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your message has been received", response.data)

    # -------------------------------------------------------------------------
    # 2. Authentication & Roles Tests
    # -------------------------------------------------------------------------
    def test_demo_login_customer(self):
        """Test 1-click demo login for customer role."""
        response = self.client.get('/demo-login/customer', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_role'), 'customer')

    def test_demo_login_farmer(self):
        """Test 1-click demo login for farmer role."""
        response = self.client.get('/demo-login/farmer', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_role'), 'farmer')

    def test_demo_login_admin(self):
        """Test 1-click demo login for admin role."""
        response = self.client.get('/demo-login/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_role'), 'admin')

    def test_role_access_control(self):
        """Test that unauthenticated users cannot access farmer or admin dashboards."""
        # Unauthenticated admin access should redirect
        res_admin = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)

        # Unauthenticated farmer access should redirect
        res_farmer = self.client.get('/farmer/dashboard', follow_redirects=False)
        self.assertEqual(res_farmer.status_code, 302)

    # -------------------------------------------------------------------------
    # 3. Shopping Cart & Checkout Process Tests
    # -------------------------------------------------------------------------
    def test_cart_workflow(self):
        """Test adding items, updating quantity, and viewing cart."""
        # Add product prod-1 (Tomatoes)
        add_res = self.client.post('/cart/add', data={
            'product_id': 'prod-1',
            'quantity': 2
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)

        # Verify in session
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart']['prod-1'], 2)

        # View cart
        cart_res = self.client.get('/cart')
        self.assertEqual(cart_res.status_code, 200)
        self.assertIn(b"Tomatoes", cart_res.data)

        # Update cart quantity
        upd_res = self.client.post('/cart/update', data={
            'product_id': 'prod-1',
            'quantity': 4
        }, follow_redirects=True)
        self.assertEqual(upd_res.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart']['prod-1'], 4)

    def test_checkout_and_order_creation(self):
        """Test complete checkout flow creates an order in orders.json and reduces stock."""
        # First add to cart
        self.client.post('/cart/add', data={'product_id': 'prod-1', 'quantity': 2})

        # Submit checkout
        checkout_res = self.client.post('/checkout', data={
            'name': 'Aarav Gupta',
            'email': 'aarav@test.com',
            'phone': '+91 9988776655',
            'address': 'B-102, Shanti Vihar, Pune',
            'payment_method': 'UPI',
            'notes': 'Call on arrival'
        }, follow_redirects=True)

        self.assertEqual(checkout_res.status_code, 200)
        self.assertIn(b"Order Successfully Placed", checkout_res.data)

        # Verify order was saved in orders.json
        orders = read_json(ORDERS_FILE)
        newest_order = orders[0]
        self.assertEqual(newest_order['customer_name'], 'Aarav Gupta')
        self.assertEqual(newest_order['payment_method'], 'UPI')

        # Test tracking that order
        track_res = self.client.get(f"/track/{newest_order['id']}")
        self.assertEqual(track_res.status_code, 200)
        self.assertIn(b"Live Order Tracking", track_res.data)

    # -------------------------------------------------------------------------
    # 4. Farmer Product & Order Management Tests
    # -------------------------------------------------------------------------
    def test_farmer_add_product(self):
        """Test farmer adding a new harvest listing."""
        # Log in as demo farmer
        self.client.get('/demo-login/farmer')

        # Add new product
        add_prod_res = self.client.post('/farmer/product/add', data={
            'name': 'Fresh Organic Green Cucumbers',
            'category': 'Vegetables',
            'price': '30.0',
            'unit': 'kg',
            'stock': '80',
            'description': 'Crisp, garden fresh cucumbers.',
            'is_organic': '1'
        }, follow_redirects=True)

        self.assertEqual(add_prod_res.status_code, 200)
        self.assertIn(b"listed on FarmDirect marketplace successfully", add_prod_res.data)

        # Check it exists in products.json
        products = read_json(PRODUCTS_FILE)
        created = [p for p in products if p['name'] == 'Fresh Organic Green Cucumbers']
        self.assertTrue(len(created) > 0)

    # -------------------------------------------------------------------------
    # 5. Admin Governance & Farmer Approval Tests
    # -------------------------------------------------------------------------
    def test_admin_farmer_approval(self):
        """Test administrator approving a pending farmer."""
        # Log in as admin
        self.client.get('/demo-login/admin')

        # Approve farmer 'u-farmer-4' (Kiran Rao, Deccan Agro Greens)
        approve_res = self.client.post('/admin/farmer/approve/u-farmer-4', follow_redirects=True)
        self.assertEqual(approve_res.status_code, 200)
        self.assertIn(b"Farmer approved successfully", approve_res.data)

        # Verify status in users.json
        users = read_json(USERS_FILE)
        kiran = [u for u in users if u['id'] == 'u-farmer-4'][0]
        self.assertEqual(kiran['status'], 'approved')


if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=================================================================")
    print(" [*] Running FarmDirect Automated Verification Test Suite")
    print("=================================================================")
    unittest.main(verbosity=2)
