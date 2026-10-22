# 🌱 FarmDirect — Farmer-to-Customer Marketplace

> A modern, attractive, and beginner-friendly web platform built with **Python (Flask)** and **JSON Database** that connects agricultural farmers directly with household consumers, eliminating greedy middlemen and ensuring farm-fresh harvest delivery.

---

## 🌟 Key Highlights & Theme

- **Palette**: Clean nature green & fresh white (`#2e7d32`, `#4caf50`, `#f8faf8`, `#ffffff`).
- **Responsive**: Seamless experience across mobile phones, tablets, and laptops.
- **Database**: 100% portable JSON storage in `data/` — no complex SQL database server setup required!
- **Beginner-Friendly**: Clean, well-commented code, modular structure, and 1-click demo logins.
- **Ready for GitHub**: Organized into separate files (`server.py`, `test_server.py`, `templates/`, `static/css/`, `static/js/`, `data/`).

---

## 📋 Features Checklist

| # | Feature | Description |
|---|---|---|
| 1 | **Home Page** | Brand logo, hero banner with search, stats counter, category pills, featured fresh produce cards, and "How it works" steps. |
| 2 | **Customer Login & Registration** | Create customer accounts, session login with secure password hashing (`Werkzeug`), address auto-fill. |
| 3 | **Farmer Login & Registration** | Register as farmer with farm name, location, and bio. Access dedicated portal. |
| 4 | **Product Marketplace** | Displays fresh vegetables, fruits, grains, and organic dairy with price/kg, stock units, and origin farm details. |
| 5 | **Search & Filters** | Search by keyword, filter by category, location/region, organic toggle, and sort by price (low/high) or newest. |
| 6 | **Shopping Cart** | Interactive cart with quantity controls (+/-), live total recalculation, free delivery threshold indicator, and clear cart option. |
| 7 | **Order Tracking** | Visual milestone stepper (*Placed &rarr; Confirmed &rarr; Packed &rarr; Out for Delivery &rarr; Delivered*) with detailed timeline log. |
| 8 | **Farmer Dashboard** | Add new crops, edit prices & stock, delete products, view incoming customer orders, and update delivery status. |
| 9 | **Admin Dashboard** | Super-admin analytics (GMV sales, total orders, active farmers), approve/reject pending farmers, delete inappropriate products/users, view customer inquiries. |
| 10 | **About Us & Contact** | Explains the mission of removing middlemen, comparison breakdown, FAQ section, and contact form saving inquiries to JSON. |
| 11 | **Payment Option** | Interactive checkout supporting **Cash on Delivery (COD)**, **UPI / QR Code**, **Credit / Debit Card**, and **Net Banking**. |

---

## 🗂️ Project Directory Structure

```text
cep/
├── server.py                # Main Flask backend server (routes, auth, cart, API)
├── test_server.py           # Automated test suite (15 unit tests)
├── requirements.txt         # Python package dependencies
├── README.md                # Project documentation and guide
├── .gitignore               # Git ignore configuration
│
├── data/                    # JSON Database (Zero SQL config needed!)
│   ├── users.json           # Customers, Farmers, and Admin accounts
│   ├── products.json        # Fresh produce catalog with photos & stock
│   ├── orders.json          # Orders placed with timeline history
│   └── messages.json        # Inquiries submitted via contact form
│
├── static/
│   ├── css/
│   │   └── style.css        # Green-and-white theme, grid, cards, responsive CSS
│   └── js/
│       └── main.js          # Cart AJAX, quantity steppers, payment toggles, toasts
│
└── templates/               # Clean Jinja2 HTML templates
    ├── base.html            # Navigation header, cart counter, alerts, footer
    ├── index.html           # Home page with hero, search, featured crops
    ├── marketplace.html     # Filterable product catalog
    ├── product_detail.html  # Single product view & farmer story
    ├── cart.html            # Shopping cart table & order breakdown
    ├── checkout.html        # Shipping address & payment method simulation
    ├── order_success.html   # Order receipt & confirmation
    ├── order_tracking.html  # Visual milestone delivery stepper
    ├── orders.html          # Customer order history
    ├── login.html           # Login page with 1-click demo login buttons
    ├── register.html        # Registration with Customer/Farmer toggle tabs
    ├── farmer_dashboard.html# Farmer inventory & order dispatch portal
    ├── farmer_add_product.html # Add / edit harvest produce form
    ├── admin_dashboard.html # Admin analytics, approvals & user management
    ├── about.html           # Mission, comparison, and core values
    └── contact.html         # Contact form, office info & FAQs
```

---

## 🚀 How to Run in VS Code

### Step 1: Open Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File &rarr; Open Folder...** and select the `cep` folder.

### Step 2: Open Terminal in VS Code
- Press `Ctrl + ~` (or `Ctrl + \``) to open the built-in terminal (PowerShell or Bash).

### Step 3: Install Required Dependencies
Ensure Flask is installed:
```powershell
pip install -r requirements.txt
```

### Step 4: Start the Server
Run `server.py`:
```powershell
python server.py
```

You will see:
```text
=================================================================
 [*] FarmDirect - Farmer-to-Customer Marketplace Server Started
 Access the website at: http://127.0.0.1:5000
=================================================================
 * Serving Flask app 'server'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Step 5: Open in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Accounts

For testing, you can use these pre-configured accounts or click the **1-Click Demo Buttons** on the `/login` page:

| Role | Email | Password | What You Can Test |
|---|---|---|---|
| **Admin** | `admin@farmdirect.com` | `admin123` | View sales GMV, approve pending farmers, remove items, manage all orders. |
| **Farmer** | `farmer.ramesh@farmdirect.com` | `farmer123` | Add new produce, change prices & stock, update customer order status (*Packed/Delivered*). |
| **Customer** | `customer.priya@gmail.com` | `customer123` | Add items to cart, checkout with COD/UPI/Card, live order milestone tracking. |

> *Tip:* You can also register your own brand-new Customer or Farmer account directly from the **Register** tab!

---

## 🧪 Running Automated Tests

Run the included verification test suite:
```powershell
python test_server.py
```
This tests all 15 endpoints (Home, Marketplace, Search, Cart, Checkout, Stock Deduction, Farmer Portal, Admin Approvals) in under 1 second.

---

## 📤 How to Upload to GitHub

Follow these steps to upload your project to GitHub:

### 1. Initialize Git Repository
In your VS Code terminal inside the project directory:
```powershell
git init
```

### 2. Stage and Commit All Files
```powershell
git add .
git commit -m "Initial commit: FarmDirect Farmer-to-Customer Marketplace"
```

### 3. Create a New Repository on GitHub
1. Go to [github.com](https://github.com) and log in.
2. Click the **+** icon in the top right &rarr; **New repository**.
3. Name it `FarmDirect` (keep it Public).
4. Do **not** check "Initialize with README" (we already have a complete one).
5. Click **Create repository**.

### 4. Link & Push to GitHub
Copy your repository URL from GitHub and run:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/FarmDirect.git
git branch -M main
git push -u origin main
```

Your project is now live on GitHub! 🎉

---

## 👨‍🌾 About FarmDirect Movement
Built with ❤️ for direct agriculture empowerment. Eliminating the unnecessary intermediary layer ensures farmers earn dignified livelihoods while consumers receive clean, chemical-free food at honest prices.
