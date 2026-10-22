"""
=============================================================================
 FarmDirect - Farmer-to-Customer Marketplace
 Backend Server (Flask + JSON Database)
=============================================================================
"""

import os
import json
import uuid
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'farmdirect-super-secret-key-change-in-production-2026'
app.config['JSON_SORT_KEYS'] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
MESSAGES_FILE = os.path.join(DATA_DIR, 'messages.json')


# -----------------------------------------------------------------------------
# JSON Database Helpers
# -----------------------------------------------------------------------------
def read_json(file_path):
    """Safely read and parse a JSON file."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def write_json(file_path, data):
    """Write data to a JSON file formatted cleanly."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    temp_file = file_path + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

# Quick lookups
def get_user_by_id(user_id):
    users = read_json(USERS_FILE)
    for u in users:
        if u.get('id') == user_id:
            return u
    return None

def get_user_by_email(email):
    users = read_json(USERS_FILE)
    for u in users:
        if u.get('email', '').strip().lower() == email.strip().lower():
            return u
    return None

def get_product_by_id(product_id):
    products = read_json(PRODUCTS_FILE)
    for p in products:
        if p.get('id') == product_id:
            return p
    return None

def get_order_by_id(order_id):
    orders = read_json(ORDERS_FILE)
    for o in orders:
        if o.get('id') == order_id:
            return o
    return None


# -----------------------------------------------------------------------------
# Authentication & Role Decorators
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in as a farmer to access this portal.", "warning")
            return redirect(url_for('login', next=request.url))
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'farmer':
            flash("Access restricted to registered farmers only.", "danger")
            return redirect(url_for('index'))
        if user.get('status') != 'approved':
            flash("Your farmer profile is currently pending administrator verification.", "info")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for('login', next=request.url))
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash("Administrator privileges required.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Context Processor (makes cart count & current user available in all templates)
# -----------------------------------------------------------------------------
@app.context_processor
def inject_global_data():
    current_user = None
    if 'user_id' in session:
        current_user = get_user_by_id(session['user_id'])
    
    # Calculate cart item count
    cart = session.get('cart', {})
    cart_count = sum(cart.values()) if isinstance(cart, dict) else 0

    return {
        'current_user': current_user,
        'cart_count': cart_count,
        'current_year': datetime.now().year
    }


# -----------------------------------------------------------------------------
# Public & Marketplace Routes
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    """Home page with hero section, categories, and featured products."""
    products = read_json(PRODUCTS_FILE)
    # Get featured products first
    featured_products = [p for p in products if p.get('is_featured')]
    if len(featured_products) < 6:
        # Fallback to latest products if not enough featured
        featured_products = products[:6]
    else:
        featured_products = featured_products[:6]

    users = read_json(USERS_FILE)
    farmers_count = len([u for u in users if u.get('role') == 'farmer' and u.get('status') == 'approved'])
    customers_count = len([u for u in users if u.get('role') == 'customer'])
    orders_count = len(read_json(ORDERS_FILE))

    return render_template(
        'index.html',
        featured_products=featured_products,
        farmers_count=farmers_count,
        customers_count=customers_count,
        orders_count=orders_count
    )


@app.route('/marketplace')
def marketplace():
    """Product marketplace with search, category, location, and price filters."""
    products = read_json(PRODUCTS_FILE)

    # Query parameters
    search_query = request.args.get('q', '').strip().lower()
    selected_category = request.args.get('category', '').strip()
    selected_location = request.args.get('location', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    organic_only = request.args.get('organic') == '1'
    sort_by = request.args.get('sort', 'default')

    # Available categories and locations for filter sidebar
    all_categories = sorted(list(set(p.get('category', 'Other') for p in products)))
    all_locations = sorted(list(set(p.get('location', '') for p in products if p.get('location'))))

    # Apply filters
    filtered = []
    for p in products:
        # Search query in name, description, farmer_name, or farm_name
        if search_query:
            target_str = f"{p.get('name', '')} {p.get('description', '')} {p.get('farmer_name', '')} {p.get('farm_name', '')} {p.get('category', '')}".lower()
            if search_query not in target_str:
                continue

        # Category
        if selected_category and p.get('category') != selected_category:
            continue

        # Location
        if selected_location and selected_location.lower() not in p.get('location', '').lower():
            continue

        # Price range
        price = float(p.get('price', 0))
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue

        # Organic
        if organic_only and not p.get('is_organic'):
            continue

        filtered.append(p)

    # Sorting
    if sort_by == 'price_low':
        filtered.sort(key=lambda x: float(x.get('price', 0)))
    elif sort_by == 'price_high':
        filtered.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
    elif sort_by == 'newest':
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return render_template(
        'marketplace.html',
        products=filtered,
        categories=all_categories,
        locations=all_locations,
        selected_category=selected_category,
        selected_location=selected_location,
        search_query=search_query,
        min_price=min_price,
        max_price=max_price,
        organic_only=organic_only,
        sort_by=sort_by,
        total_count=len(filtered)
    )


@app.route('/product/<product_id>')
def product_detail(product_id):
    """Detailed view for a specific product."""
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('marketplace'))

    # Get farmer profile
    farmer = get_user_by_id(product.get('farmer_id'))

    # Related products from same category or farmer
    all_products = read_json(PRODUCTS_FILE)
    related_products = [
        p for p in all_products 
        if p.get('id') != product_id and (p.get('category') == product.get('category') or p.get('farmer_id') == product.get('farmer_id'))
    ][:4]

    return render_template('product_detail.html', product=product, farmer=farmer, related_products=related_products)


@app.route('/about')
def about():
    """About us page explaining the mission of FarmDirect."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact us page and submission handler."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('contact'))

        messages = read_json(MESSAGES_FILE)
        new_msg = {
            'id': f"msg-{uuid.uuid4().hex[:6]}",
            'name': name,
            'email': email,
            'subject': subject or 'General Inquiry',
            'message': message,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        messages.append(new_msg)
        write_json(MESSAGES_FILE, messages)

        flash("Thank you! Your message has been received. Our team will contact you shortly.", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')


# -----------------------------------------------------------------------------
# User Authentication (Customer, Farmer, Admin)
# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for Customer, Farmer, and Admin with demo quick-login."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = get_user_by_email(email)
        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash("Invalid email or password. Please check your credentials.", "danger")
            return render_template('login.html', email=email)

        # Farmer approval check
        if user.get('role') == 'farmer' and user.get('status') == 'pending':
            flash("Your farmer account is currently awaiting admin verification. Please wait for approval.", "warning")
            return render_template('login.html', email=email)

        # Login successful - populate session
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        session['user_email'] = user['email']

        flash(f"Welcome back, {user['name']}!", "success")

        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)

        # Redirect according to role
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        else:
            return redirect(url_for('marketplace'))

    return render_template('login.html')


@app.route('/demo-login/<role>')
def demo_login(role):
    """Convenient 1-click login for testing Admin, Farmer, or Customer roles."""
    demo_emails = {
        'admin': 'admin@farmdirect.com',
        'farmer': 'farmer.ramesh@farmdirect.com',
        'customer': 'customer.priya@gmail.com'
    }
    target_email = demo_emails.get(role)
    if not target_email:
        flash("Invalid demo role selected.", "danger")
        return redirect(url_for('login'))

    user = get_user_by_email(target_email)
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        session['user_email'] = user['email']
        flash(f"Logged in as Demo {role.capitalize()}: {user['name']}", "info")
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        else:
            return redirect(url_for('marketplace'))
    
    flash("Demo user not found.", "danger")
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register either as a Customer or as a Farmer."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        role = request.form.get('role', 'customer').strip().lower()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template('register.html', role=role)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html', role=role)

        existing_user = get_user_by_email(email)
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        users = read_json(USERS_FILE)
        new_user = {
            'id': f"u-{uuid.uuid4().hex[:8]}",
            'name': name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': 'farmer' if role == 'farmer' else 'customer',
            'phone': phone,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if role == 'farmer':
            new_user['farm_name'] = request.form.get('farm_name', '').strip() or f"{name}'s Farm"
            new_user['location'] = request.form.get('location', '').strip() or 'Local Region'
            new_user['bio'] = request.form.get('bio', '').strip() or 'Direct farm producer.'
            # To make testing easy, auto-approve or keep pending for admin approval
            # Let's auto-approve new farmers so beginners can try immediately, but allow admin to manage!
            new_user['status'] = 'approved'
            users.append(new_user)
            write_json(USERS_FILE, users)

            flash("Farmer account registered successfully! You are now logged in.", "success")
        else:
            new_user['address'] = request.form.get('address', '').strip()
            new_user['status'] = 'approved'
            users.append(new_user)
            write_json(USERS_FILE, users)

            flash("Customer account created successfully! You are now logged in.", "success")

        # Automatically log in the user
        session['user_id'] = new_user['id']
        session['user_name'] = new_user['name']
        session['user_role'] = new_user['role']
        session['user_email'] = new_user['email']

        if new_user['role'] == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        return redirect(url_for('marketplace'))

    role_param = request.args.get('role', 'customer')
    return render_template('register.html', default_role=role_param)


@app.route('/logout')
def logout():
    """Clear session and log user out."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))


# -----------------------------------------------------------------------------
# Shopping Cart & Checkout
# -----------------------------------------------------------------------------
@app.route('/cart')
def view_cart():
    """View shopping cart with itemized breakdown and delivery calculations."""
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0.0

    for product_id, qty in cart.items():
        product = get_product_by_id(product_id)
        if product:
            item_total = float(product.get('price', 0)) * qty
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'item_total': item_total
            })

    # Standard flat delivery fee: free if above 500, else 40
    delivery_fee = 0.0 if (subtotal >= 500 or subtotal == 0) else 40.0
    grand_total = subtotal + delivery_fee

    return render_template(
        'cart.html',
        cart_items=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        grand_total=grand_total
    )


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add a product to cart or increment quantity."""
    product_id = request.form.get('product_id')
    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    product = get_product_by_id(product_id)
    if not product:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Product not found.'}), 404
        flash("Product not found.", "warning")
        return redirect(url_for('marketplace'))

    # Check available stock
    stock = int(product.get('stock', 0))
    if stock <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'This product is out of stock.'}), 400
        flash("Sorry, this item is currently out of stock.", "warning")
        return redirect(request.referrer or url_for('marketplace'))

    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}

    current_qty = session['cart'].get(product_id, 0)
    new_qty = current_qty + quantity
    if new_qty > stock:
        new_qty = stock
        flash(f"Adjusted quantity to max available stock ({stock}).", "info")

    session['cart'][product_id] = new_qty
    session.modified = True

    total_cart_items = sum(session['cart'].values())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f"Added '{product['name']}' to cart!",
            'cart_count': total_cart_items
        })

    flash(f"Added {product['name']} to your cart.", "success")
    return redirect(request.referrer or url_for('view_cart'))


@app.route('/cart/update', methods=['POST'])
def update_cart():
    """Update quantity for a cart item or remove if 0."""
    product_id = request.form.get('product_id')
    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    cart = session.get('cart', {})
    if product_id in cart:
        if quantity <= 0:
            del cart[product_id]
            flash("Item removed from cart.", "info")
        else:
            product = get_product_by_id(product_id)
            stock = int(product.get('stock', 999)) if product else 999
            cart[product_id] = min(quantity, stock)
            flash("Cart updated successfully.", "success")
        session['cart'] = cart
        session.modified = True

    return redirect(url_for('view_cart'))


@app.route('/cart/remove/<product_id>', methods=['POST', 'GET'])
def remove_from_cart(product_id):
    """Remove a single product from cart."""
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
        session.modified = True
        flash("Item removed from cart.", "info")

    return redirect(url_for('view_cart'))


@app.route('/cart/clear')
def clear_cart():
    """Clear all items in cart."""
    session['cart'] = {}
    session.modified = True
    flash("Cart cleared.", "info")
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page with customer details & payment simulation."""
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty. Add fresh items from the marketplace first!", "warning")
        return redirect(url_for('marketplace'))

    # Build cart items
    cart_items = []
    subtotal = 0.0
    for product_id, qty in cart.items():
        product = get_product_by_id(product_id)
        if product:
            item_total = float(product.get('price', 0)) * qty
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'item_total': item_total
            })

    if not cart_items:
        session['cart'] = {}
        flash("Your cart had unavailable items. Please browse fresh produce.", "warning")
        return redirect(url_for('marketplace'))

    delivery_fee = 0.0 if subtotal >= 500 else 40.0
    grand_total = subtotal + delivery_fee

    current_user = get_user_by_id(session.get('user_id')) if 'user_id' in session else None

    if request.method == 'POST':
        # Collect customer and shipping details
        customer_name = request.form.get('name', '').strip()
        customer_email = request.form.get('email', '').strip()
        customer_phone = request.form.get('phone', '').strip()
        delivery_address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', 'COD').strip()
        delivery_notes = request.form.get('notes', '').strip()

        if not customer_name or not customer_email or not customer_phone or not delivery_address:
            flash("Please fill in all shipping details.", "danger")
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                grand_total=grand_total,
                user=current_user
            )

        # Build order item list and reduce product stock
        products = read_json(PRODUCTS_FILE)
        order_items = []
        for item in cart_items:
            p = item['product']
            qty = item['quantity']
            order_items.append({
                'product_id': p['id'],
                'name': p['name'],
                'price': float(p['price']),
                'quantity': qty,
                'unit': p.get('unit', 'kg'),
                'farmer_id': p.get('farmer_id'),
                'farmer_name': p.get('farmer_name', 'Local Farmer'),
                'farm_name': p.get('farm_name', 'FarmDirect Source'),
                'subtotal': float(p['price']) * qty
            })

            # Update stock in products list
            for prod in products:
                if prod['id'] == p['id']:
                    prod['stock'] = max(0, int(prod.get('stock', 0)) - qty)
                    break

        write_json(PRODUCTS_FILE, products)

        # Payment status simulation
        payment_status = "Paid" if payment_method in ['UPI', 'Card', 'NetBanking'] else "Pending (Cash On Delivery)"

        # Create Order
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
        new_order = {
            'id': order_id,
            'customer_id': session.get('user_id', 'guest'),
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'delivery_address': delivery_address,
            'items': order_items,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
            'payment_method': payment_method,
            'payment_status': payment_status,
            'order_status': 'Confirmed',
            'notes': delivery_notes,
            'timeline': [
                {'status': 'Placed', 'time': now_str, 'note': f"Order received. Payment method: {payment_method}."},
                {'status': 'Confirmed', 'time': now_str, 'note': "Order confirmed directly with participating farmers."}
            ],
            'created_at': now_str
        }

        orders = read_json(ORDERS_FILE)
        orders.insert(0, new_order)  # Newest first
        write_json(ORDERS_FILE, orders)

        # Clear cart
        session['cart'] = {}
        session.modified = True

        flash(f"Order #{order_id} placed successfully! Thank you for supporting our local farmers directly.", "success")
        return redirect(url_for('order_success', order_id=order_id))

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        grand_total=grand_total,
        user=current_user
    )


@app.route('/order-success/<order_id>')
def order_success(order_id):
    """Order confirmation and receipt summary page."""
    order = get_order_by_id(order_id)
    if not order:
        flash("Order not found.", "warning")
        return redirect(url_for('index'))
    return render_template('order_success.html', order=order)


# -----------------------------------------------------------------------------
# Order Tracking & Customer Orders
# -----------------------------------------------------------------------------
@app.route('/track/<order_id>')
def track_order(order_id):
    """Visual tracking page showing milestone progress (Placed -> Delivered)."""
    order = get_order_by_id(order_id)
    if not order:
        flash(f"Order '{order_id}' was not found. Please verify your order number.", "warning")
        return redirect(url_for('marketplace'))

    # Status sequence for stepper UI
    statuses = ['Placed', 'Confirmed', 'Packed', 'Out for Delivery', 'Delivered']
    current_status = order.get('order_status', 'Placed')
    try:
        active_step_index = statuses.index(current_status)
    except ValueError:
        active_step_index = 0

    return render_template(
        'order_tracking.html',
        order=order,
        statuses=statuses,
        active_step_index=active_step_index
    )


@app.route('/orders')
@login_required
def customer_orders():
    """List of orders placed by the currently logged-in customer."""
    user_id = session.get('user_id')
    all_orders = read_json(ORDERS_FILE)
    user_email = session.get('user_email', '').lower()

    # Match by customer_id or customer_email
    customer_orders_list = [
        o for o in all_orders
        if o.get('customer_id') == user_id or o.get('customer_email', '').lower() == user_email
    ]

    return render_template('orders.html', orders=customer_orders_list)


# -----------------------------------------------------------------------------
# Farmer Dashboard & Product Management
# -----------------------------------------------------------------------------
@app.route('/farmer/dashboard')
@farmer_required
def farmer_dashboard():
    """Farmer control center: products inventory and customer orders."""
    farmer_id = session['user_id']
    farmer = get_user_by_id(farmer_id)
    all_products = read_json(PRODUCTS_FILE)
    all_orders = read_json(ORDERS_FILE)

    farmer_products = [p for p in all_products if p.get('farmer_id') == farmer_id]

    # Find orders containing items from this farmer
    farmer_orders = []
    total_revenue = 0.0
    items_sold = 0

    for order in all_orders:
        farmer_items = [item for item in order.get('items', []) if item.get('farmer_id') == farmer_id]
        if farmer_items:
            order_farmer_subtotal = sum(i.get('subtotal', 0.0) for i in farmer_items)
            total_revenue += order_farmer_subtotal
            items_sold += sum(i.get('quantity', 0) for i in farmer_items)
            farmer_orders.append({
                'order_id': order.get('id'),
                'customer_name': order.get('customer_name'),
                'customer_phone': order.get('customer_phone'),
                'delivery_address': order.get('delivery_address'),
                'order_status': order.get('order_status'),
                'created_at': order.get('created_at'),
                'items': farmer_items,
                'total_amount': order_farmer_subtotal
            })

    low_stock_count = len([p for p in farmer_products if int(p.get('stock', 0)) <= 20])

    return render_template(
        'farmer_dashboard.html',
        farmer=farmer,
        products=farmer_products,
        orders=farmer_orders,
        total_products=len(farmer_products),
        total_revenue=total_revenue,
        items_sold=items_sold,
        low_stock_count=low_stock_count
    )


@app.route('/farmer/product/add', methods=['GET', 'POST'])
@farmer_required
def farmer_add_product():
    """Add a new fresh produce item."""
    farmer = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', 'Vegetables').strip()
        price = float(request.form.get('price', 0))
        unit = request.form.get('unit', 'kg').strip()
        stock = int(request.form.get('stock', 0))
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_organic = request.form.get('is_organic') == '1'

        # Default high-res fallback image if not provided
        default_images = {
            'Vegetables': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80',
            'Fruits': 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&auto=format&fit=crop&q=80',
            'Grains': 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&auto=format&fit=crop&q=80',
            'Dairy & Organic': 'https://images.unsplash.com/photo-1527153857715-3908f2ae5e81?w=600&auto=format&fit=crop&q=80'
        }
        if not image_url:
            image_url = default_images.get(category, default_images['Vegetables'])

        new_product = {
            'id': f"prod-{uuid.uuid4().hex[:6]}",
            'farmer_id': farmer['id'],
            'farmer_name': farmer['name'],
            'farm_name': farmer.get('farm_name', f"{farmer['name']}'s Farm"),
            'location': farmer.get('location', 'Direct Farm'),
            'name': name,
            'category': category,
            'price': price,
            'unit': unit,
            'stock': stock,
            'description': description,
            'image_url': image_url,
            'is_organic': is_organic,
            'is_featured': False,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        products = read_json(PRODUCTS_FILE)
        products.insert(0, new_product)
        write_json(PRODUCTS_FILE, products)

        flash(f"Produce '{name}' listed on FarmDirect marketplace successfully!", "success")
        return redirect(url_for('farmer_dashboard'))

    return render_template('farmer_add_product.html', farmer=farmer, product=None)


@app.route('/farmer/product/edit/<product_id>', methods=['GET', 'POST'])
@farmer_required
def farmer_edit_product(product_id):
    """Edit existing product details."""
    farmer = get_user_by_id(session['user_id'])
    products = read_json(PRODUCTS_FILE)

    target_idx = None
    for idx, p in enumerate(products):
        if p.get('id') == product_id and p.get('farmer_id') == farmer['id']:
            target_idx = idx
            break

    if target_idx is None:
        flash("Product not found or unauthorized.", "danger")
        return redirect(url_for('farmer_dashboard'))

    product = products[target_idx]

    if request.method == 'POST':
        product['name'] = request.form.get('name', '').strip() or product['name']
        product['category'] = request.form.get('category', product['category']).strip()
        product['price'] = float(request.form.get('price', product['price']))
        product['unit'] = request.form.get('unit', product['unit']).strip()
        product['stock'] = int(request.form.get('stock', product['stock']))
        product['description'] = request.form.get('description', '').strip()
        if request.form.get('image_url', '').strip():
            product['image_url'] = request.form.get('image_url').strip()
        product['is_organic'] = request.form.get('is_organic') == '1'

        products[target_idx] = product
        write_json(PRODUCTS_FILE, products)

        flash("Product updated successfully!", "success")
        return redirect(url_for('farmer_dashboard'))

    return render_template('farmer_add_product.html', farmer=farmer, product=product)


@app.route('/farmer/product/delete/<product_id>', methods=['POST'])
@farmer_required
def farmer_delete_product(product_id):
    """Delete a farmer's product."""
    farmer_id = session['user_id']
    products = read_json(PRODUCTS_FILE)
    filtered = [p for p in products if not (p.get('id') == product_id and p.get('farmer_id') == farmer_id)]

    if len(filtered) < len(products):
        write_json(PRODUCTS_FILE, filtered)
        flash("Product deleted from your catalog.", "info")
    else:
        flash("Product could not be removed.", "warning")

    return redirect(url_for('farmer_dashboard'))


@app.route('/farmer/order/status/<order_id>', methods=['POST'])
@farmer_required
def farmer_update_order_status(order_id):
    """Farmer updates order status (Confirmed, Packed, Out for Delivery, Delivered)."""
    new_status = request.form.get('status', '').strip()
    note_text = request.form.get('note', '').strip()

    valid_statuses = ['Confirmed', 'Packed', 'Out for Delivery', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        flash("Invalid status choice.", "danger")
        return redirect(url_for('farmer_dashboard'))

    orders = read_json(ORDERS_FILE)
    updated = False
    for o in orders:
        if o.get('id') == order_id:
            o['order_status'] = new_status
            if 'timeline' not in o:
                o['timeline'] = []
            o['timeline'].append({
                'status': new_status,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'note': note_text or f"Status updated to '{new_status}' by farmer."
            })
            updated = True
            break

    if updated:
        write_json(ORDERS_FILE, orders)
        flash(f"Order #{order_id} status updated to '{new_status}'.", "success")
    else:
        flash("Order not found.", "danger")

    return redirect(url_for('farmer_dashboard'))


# -----------------------------------------------------------------------------
# Admin Dashboard & Governance
# -----------------------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard: user management, farmer approvals, statistics."""
    users = read_json(USERS_FILE)
    products = read_json(PRODUCTS_FILE)
    orders = read_json(ORDERS_FILE)
    messages = read_json(MESSAGES_FILE)

    # Key statistics
    total_sales = sum(float(o.get('grand_total', 0)) for o in orders)
    total_orders = len(orders)
    total_farmers = len([u for u in users if u.get('role') == 'farmer'])
    pending_farmers = [u for u in users if u.get('role') == 'farmer' and u.get('status') == 'pending']
    total_customers = len([u for u in users if u.get('role') == 'customer'])
    total_products = len(products)

    # Category breakdown for chart/progress bar
    categories_count = {}
    for p in products:
        cat = p.get('category', 'Other')
        categories_count[cat] = categories_count.get(cat, 0) + 1

    return render_template(
        'admin_dashboard.html',
        users=users,
        products=products,
        orders=orders,
        messages=messages,
        total_sales=total_sales,
        total_orders=total_orders,
        total_farmers=total_farmers,
        pending_farmers=pending_farmers,
        total_customers=total_customers,
        total_products=total_products,
        categories_count=categories_count
    )


@app.route('/admin/farmer/approve/<user_id>', methods=['POST'])
@admin_required
def admin_approve_farmer(user_id):
    """Admin approves a registered farmer."""
    users = read_json(USERS_FILE)
    updated = False
    for u in users:
        if u.get('id') == user_id and u.get('role') == 'farmer':
            u['status'] = 'approved'
            updated = True
            break
    if updated:
        write_json(USERS_FILE, users)
        flash("Farmer approved successfully! They can now log in and list produce.", "success")
    else:
        flash("Farmer account not found.", "warning")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/farmer/reject/<user_id>', methods=['POST'])
@admin_required
def admin_reject_farmer(user_id):
    """Admin rejects/removes a farmer application."""
    users = read_json(USERS_FILE)
    filtered = [u for u in users if not (u.get('id') == user_id and u.get('role') == 'farmer')]
    write_json(USERS_FILE, filtered)
    flash("Farmer application was rejected and removed.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/product/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    """Admin removes any product from marketplace."""
    products = read_json(PRODUCTS_FILE)
    filtered = [p for p in products if p.get('id') != product_id]
    write_json(PRODUCTS_FILE, filtered)
    flash("Product removed from platform.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/user/delete/<user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Admin deletes a user account (except active admin)."""
    if user_id == session.get('user_id'):
        flash("Cannot delete your own active administrator account.", "danger")
        return redirect(url_for('admin_dashboard'))

    users = read_json(USERS_FILE)
    filtered = [u for u in users if u.get('id') != user_id]
    write_json(USERS_FILE, filtered)
    flash("User account deleted.", "info")
    return redirect(url_for('admin_dashboard'))


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', not_found=True), 404

@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Internal Server Error</h1><p>Something went wrong on the server.</p>", 500


# -----------------------------------------------------------------------------
# Main Execution Entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=================================================================")
    print(" [*] FarmDirect - Farmer-to-Customer Marketplace Server Started")
    print(" Access the website at: http://127.0.0.1:5000")
    print(" Demo Logins:")
    print("   - Admin:    admin@farmdirect.com          / admin123")
    print("   - Farmer:   farmer.ramesh@farmdirect.com  / farmer123")
    print("   - Customer: customer.priya@gmail.com      / customer123")
    print("=================================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
