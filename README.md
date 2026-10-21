# 💳 PayPal POS & Fintech Hub

A modern cross-platform **Point of Sale (POS) Checkout & Wallet Management System** built with **Python & Flet (Flutter engine)**.

Designed for retail stores, e-commerce checkouts, and fintech peer-to-peer transfers with real-time **PayPal REST API** integration and **Dynamic QR Code Checkout**.

---

## 🌟 Key Features

### 1. 🛒 Point of Sale (POS) & E-Commerce Checkout
- **Interactive Product Catalog**: Real-time filtering by category (Electronics, Beverages, Accessories, Services) and live search.
- **Dynamic Shopping Cart**: Instant item quantity adjustments, subtotal, configurable tax (e.g. 8%), and order totals.
- **Multi-Channel Checkout**:
  - **PayPal Live / Sandbox API**: Automatically generates PayPal orders, creates instant scannable payment QR codes, and supports customer payment verification & order capture.
  - **Wallet Balance**: Instantly debit from local merchant wallet balance.
  - **Walk-in Cash Tender**: POS cash payment with automatic inventory deduction.
- **Official Digital Receipts**: Printable order receipts with line items, tax breakdowns, order reference IDs, and timestamps.

### 2. 👛 Wallet & Peer-to-Peer (P2P) Transfers
- **Real-Time Available Balance**: Live wallet balance tracking across multi-currencies ($ USD, € EUR, £ GBP).
- **Send Money**: Instant P2P transfers to any recipient email with balance protection and transaction logging.
- **Request / Receive Money**: Generates dynamic scannable PayPal QR codes and payment requests.
- **Top-up & Withdraw**: Easily deposit simulated bank funds or withdraw to linked accounts.

### 3. 🧾 Ledger & Transaction History
- Comprehensive searchable audit ledger for all transaction types (POS sales, P2P sent, P2P received, deposits, withdrawals).
- Color-coded status pills and amount badges.
- Instant itemized modal view with receipt breakdowns.
- **One-Click Export to CSV** (`transactions_export.csv`).

### 4. 📦 Stock & Catalog Management
- Add, update, and delete products in the catalog.
- Low-stock automatic alerts (highlighting products with `< 10` units left).
- Automatic inventory depletion when items are sold.

### 5. ⚙️ PayPal REST API & Simulator Engine
- Seamless **Simulation / Mock Mode** active by default for local testing with zero API key requirement.
- Supports real **PayPal Sandbox** and **Live Production** environments.
- One-click **"Test API Connection"** button to verify PayPal Developer credentials against PayPal's OAuth 2.0 servers.
- Dark mode & Light mode theme toggle.

---

## 🚀 Getting Started

### Quick Start (Windows)
Double-click either of the starter files:
- **`run.bat`**: Launches as a native **Windows Desktop App**.
- **`run_web.bat`**: Launches as a responsive **Web Application** in your default browser.

### Command Line
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Launch native desktop app
python main.py

# Or launch web browser mode
python main.py --web
```

---

## 🔧 Configuring PayPal Credentials (Optional)
If you have a PayPal Developer account:
1. Go to [developer.paypal.com](https://developer.paypal.com/) -> **Apps & Credentials**.
2. Create or copy a **Sandbox** or **Live** App's **Client ID** and **Client Secret**.
3. In the application, navigate to the **Settings** tab.
4. Paste your **Client ID** and **Client Secret**.
5. Click **Test API Connection** to verify connection with PayPal's servers.
6. Toggle off **Simulation Mode** to process real PayPal Sandbox orders!

---

## 📁 Project Architecture
```
Paypal/
├── config.py                 # Configuration loader and default variables
├── database.py               # SQLite schema, transactions, products & wallet queries
├── paypal_service.py         # PayPal REST API OAuth, Orders, Capture & Simulator
├── qr_service.py             # In-memory QR code generator using qrcode + Pillow
├── views/
│   ├── dashboard_view.py     # Summary metrics, quick actions & recent feed
│   ├── pos_view.py           # Product catalog, dynamic cart & checkout dialog
│   ├── wallet_view.py        # P2P transfers, QR payment generation & banking
│   ├── transactions_view.py  # Filterable ledger, receipts & CSV exporter
│   ├── inventory_view.py     # Stock manager with low-stock alerts
│   └── settings_view.py      # PayPal credentials, store profile & diagnostics
├── main.py                   # Responsive Flet UI shell & navigation rail
├── run.bat                   # 1-Click native desktop launcher
├── run_web.bat               # 1-Click web browser launcher
└── requirements.txt          # Dependencies list
```
