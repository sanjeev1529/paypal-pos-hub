import json
import flet as ft
import database
from paypal_service import paypal_service
from qr_service import generate_qr_bytes

def get_icon(name: str):
    name_clean = (name or "SHOPPING_BAG").replace("-", "_").upper()
    return getattr(ft.Icons, name_clean, ft.Icons.SHOPPING_BAG)

class PosView(ft.Container):
    def __init__(self, page: ft.Page, on_transaction_completed=None):
        super().__init__(expand=True)
        self.app_page = page
        self.on_transaction_completed = on_transaction_completed
        self.cart = {}  # {product_id: {"product": dict, "quantity": int}}
        self.selected_category = "All"
        self.search_term = ""
        self.padding = ft.Padding.all(16)
        
        # UI Component references
        self.products_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=240,
            child_aspect_ratio=0.75,
            spacing=12,
            run_spacing=12,
        )
        self.cart_items_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.subtotal_text = ft.Text("$0.00", size=14, weight=ft.FontWeight.BOLD)
        self.tax_text = ft.Text("$0.00", size=14)
        self.total_text = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color="#003087")
        self.checkout_btn = ft.FilledButton(
            "Checkout ($0.00)",
            icon=ft.Icons.PAYMENTS,
            style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
            disabled=True,
            on_click=self.open_checkout_dialog
        )

        self.content = self.build_ui()
        self.load_products()

    def build_ui(self):
        # Category Tabs
        categories = ["All", "Electronics", "Beverages", "Accessories", "Services"]
        cat_chips = []
        for cat in categories:
            is_sel = cat == self.selected_category
            cat_chips.append(
                ft.FilledTonalButton(
                    cat,
                    style=ft.ButtonStyle(
                        bgcolor="#003087" if is_sel else ft.Colors.SURFACE_CONTAINER_HIGH,
                        color=ft.Colors.WHITE if is_sel else ft.Colors.ON_SURFACE
                    ),
                    on_click=lambda _, c=cat: self.select_category(c)
                )
            )

        search_field = ft.TextField(
            hint_text="Search catalog or SKU...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.BorderRadius.all(10),
            expand=True,
            on_change=self.on_search_change
        )

        left_panel = ft.Column([
            ft.Row([
                ft.Text("Point of Sale & Catalog", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                search_field
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row(cat_chips, scroll=ft.ScrollMode.AUTO, spacing=8),
            ft.Divider(height=10),
            self.products_grid
        ], expand=True, spacing=12)

        # Right Cart Drawer
        cart_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.SHOPPING_CART, color="#003087"),
                        ft.Text("Current Order", size=18, weight=ft.FontWeight.BOLD),
                    ], spacing=8),
                    ft.TextButton("Clear", icon=ft.Icons.DELETE_OUTLINE, on_click=self.clear_cart)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10),
                self.cart_items_col,
                ft.Divider(height=10),
                # Order summary
                ft.Column([
                    ft.Row([ft.Text("Subtotal:", color=ft.Colors.GREY_600), self.subtotal_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Tax (8%):", color=ft.Colors.GREY_600), self.tax_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=8),
                    ft.Row([ft.Text("Total Due:", size=16, weight=ft.FontWeight.BOLD), self.total_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    self.checkout_btn
                ], spacing=6)
            ], expand=True),
            width=340,
            padding=ft.Padding.all(16),
            border_radius=ft.BorderRadius.all(16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        return ft.Row([left_panel, cart_panel], expand=True, spacing=16)

    def safe_update(self):
        try:
            self.update()
        except:
            pass

    def select_category(self, cat: str):
        self.selected_category = cat
        self.load_products()
        self.content = self.build_ui()
        self.safe_update()

    def on_search_change(self, e):
        self.search_term = e.control.value
        self.load_products()

    def load_products(self):
        products = database.get_products(
            category=self.selected_category if self.selected_category != "All" else None,
            search=self.search_term
        )
        self.products_grid.controls.clear()

        for prod in products:
            in_stock = prod["stock"] > 0
            stock_color = ft.Colors.GREEN_700 if prod["stock"] > 10 else (ft.Colors.ORANGE_700 if in_stock else ft.Colors.RED_700)
            stock_label = f"{prod['stock']} in stock" if in_stock else "Out of Stock"

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(get_icon(prod["icon"]), color="#003087", size=24),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=ft.Padding.all(10),
                            border_radius=ft.BorderRadius.all(10)
                        ),
                        ft.Container(
                            content=ft.Text(stock_label, size=10, weight=ft.FontWeight.BOLD, color=stock_color),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            border_radius=ft.BorderRadius.all(4),
                            bgcolor=ft.Colors.GREEN_50 if prod['stock'] > 10 else ft.Colors.ORANGE_50
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(prod["name"], size=13, weight=ft.FontWeight.BOLD, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"SKU: {prod['sku']}", size=11, color=ft.Colors.GREY_600),
                    ft.Text(f"${prod['price']:.2f}", size=16, weight=ft.FontWeight.BOLD, color="#003087"),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        "+ Add",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        disabled=not in_stock,
                        style=ft.ButtonStyle(
                            bgcolor="#003087" if in_stock else ft.Colors.GREY_300,
                            color=ft.Colors.WHITE
                        ),
                        on_click=lambda _, p=prod: self.add_to_cart(p)
                    )
                ], spacing=6),
                padding=ft.Padding.all(14),
                border_radius=ft.BorderRadius.all(14),
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
            )
            self.products_grid.controls.append(card)

        self.safe_update()

    def add_to_cart(self, prod: dict):
        pid = prod["id"]
        if pid in self.cart:
            if self.cart[pid]["quantity"] < prod["stock"]:
                self.cart[pid]["quantity"] += 1
            else:
                self.show_snack("Cannot add more: Max available stock reached.")
                return
        else:
            self.cart[pid] = {"product": prod, "quantity": 1}

        self.refresh_cart()

    def update_quantity(self, pid: int, delta: int):
        if pid in self.cart:
            new_qty = self.cart[pid]["quantity"] + delta
            if new_qty <= 0:
                del self.cart[pid]
            elif new_qty > self.cart[pid]["product"]["stock"]:
                self.show_snack("Cannot exceed available inventory.")
                return
            else:
                self.cart[pid]["quantity"] = new_qty
        self.refresh_cart()

    def remove_item(self, pid: int):
        if pid in self.cart:
            del self.cart[pid]
        self.refresh_cart()

    def clear_cart(self, _=None):
        self.cart.clear()
        self.refresh_cart()

    def refresh_cart(self):
        self.cart_items_col.controls.clear()
        subtotal = 0.0

        if not self.cart:
            self.cart_items_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=48, color=ft.Colors.GREY_400),
                        ft.Text("Cart is currently empty", color=ft.Colors.GREY_500),
                        ft.Text("Select products from the left to start an order", size=12, color=ft.Colors.GREY_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.all(20)
                )
            )
            self.checkout_btn.disabled = True
            self.checkout_btn.text = "Checkout ($0.00)"
        else:
            for pid, item in self.cart.items():
                p = item["product"]
                qty = item["quantity"]
                line_total = p["price"] * qty
                subtotal += line_total

                row = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(p["name"], size=13, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"${p['price']:.2f} ea", size=11, color=ft.Colors.GREY_600),
                        ], expand=True, spacing=2),
                        ft.Row([
                            ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self.update_quantity(i, -1)),
                            ft.Text(str(qty), size=13, weight=ft.FontWeight.BOLD),
                            ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self.update_quantity(i, 1)),
                        ], spacing=0),
                        ft.Text(f"${line_total:.2f}", size=13, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.RED_400, on_click=lambda _, i=pid: self.remove_item(i))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.all(8),
                    border_radius=ft.BorderRadius.all(8),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW
                )
                self.cart_items_col.controls.append(row)

            tax = subtotal * (float(database.get_setting("tax_rate", "8.0")) / 100.0)
            total = subtotal + tax

            self.subtotal_text.value = f"${subtotal:,.2f}"
            self.tax_text.value = f"${tax:,.2f}"
            self.total_text.value = f"${total:,.2f}"
            self.checkout_btn.disabled = False
            self.checkout_btn.text = f"Checkout (${total:,.2f})"

        self.safe_update()

    def open_checkout_dialog(self, _):
        if not self.cart:
            return

        subtotal = sum(item["product"]["price"] * item["quantity"] for item in self.cart.values())
        tax = subtotal * (float(database.get_setting("tax_rate", "8.0")) / 100.0)
        total = round(subtotal + tax, 2)
        wallet = database.get_wallet()

        # Generate PayPal order
        order = paypal_service.create_order(
            amount=total,
            currency="USD",
            items=[{"name": item["product"]["name"], "qty": item["quantity"], "price": item["product"]["price"]} for item in self.cart.values()],
            description="Point of Sale Order"
        )

        qr_img_bytes = generate_qr_bytes(order["qr_payload"], box_size=5)

        status_banner = ft.Text(f"Mode: {order['mode']}", size=12, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)

        def complete_payment(method: str):
            if method == "paypal":
                capture_res = paypal_service.capture_order(order["order_id"])
                if not capture_res["success"]:
                    self.show_snack(f"Payment failed: {capture_res.get('message')}")
                    return
                database.update_wallet_balance(total)
                pay_ref = order["order_id"]
            elif method == "wallet":
                if wallet["balance"] < total:
                    self.show_snack("Insufficient wallet balance for this purchase.")
                    return
                database.update_wallet_balance(-total)
                pay_ref = "WALLET-DIRECT"
            elif method == "cash":
                database.update_wallet_balance(total)
                pay_ref = "CASH-REGISTER"

            items_summary = []
            for item in self.cart.values():
                database.deduct_product_stock(item["product"]["id"], item["quantity"])
                items_summary.append({
                    "name": item["product"]["name"],
                    "qty": item["quantity"],
                    "price": item["product"]["price"],
                    "subtotal": round(item["product"]["price"] * item["quantity"], 2)
                })

            tx_id = database.create_transaction(
                tx_type="pos_sale",
                amount=total,
                currency="USD",
                fee=round(total * 0.029 + 0.30, 2) if method == "paypal" else 0.0,
                net=total,
                status="completed",
                counterparty=f"POS Customer ({method.upper()})",
                paypal_order_id=pay_ref,
                reference_note=f"POS Sale #{order['order_id'][:12]} ({len(items_summary)} items)",
                items_list=items_summary
            )

            self.app_page.pop_dialog()

            self.clear_cart()
            self.load_products()

            if self.on_transaction_completed:
                self.on_transaction_completed()

            self.show_receipt(tx_id, method, items_summary, subtotal, tax, total, pay_ref)

        checkout_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.POINT_OF_SALE, color="#003087"),
                ft.Text("Complete Order Checkout", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("ORDER TOTAL DUE", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
                                ft.Text(f"${total:,.2f}", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ], spacing=2),
                            ft.Container(
                                content=status_banner,
                                bgcolor=ft.Colors.WHITE,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=ft.BorderRadius.all(6)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.Padding.all(16),
                        border_radius=ft.BorderRadius.all(12),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#003087", "#0079C1"]
                        )
                    ),
                    ft.Text("Option 1: Scan & Pay with PayPal", weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.Container(
                            content=ft.Image(src=qr_img_bytes, width=140, height=140),
                            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=ft.BorderRadius.all(8),
                            padding=ft.Padding.all(6)
                        ),
                        ft.Column([
                            ft.Text(f"Order: {order['order_id'][:16]}...", size=12, weight=ft.FontWeight.W_600),
                            ft.Text("Scan this QR code with your mobile or click to simulate approval:", size=11, color=ft.Colors.GREY_600),
                            ft.FilledButton(
                                "Simulate / Confirm PayPal Payment",
                                icon=ft.Icons.CHECK_CIRCLE,
                                style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
                                on_click=lambda _: complete_payment("paypal")
                            )
                        ], expand=True, spacing=6)
                    ], spacing=12),
                    ft.Divider(height=16),
                    ft.Text("Option 2: Alternative Tender", weight=ft.FontWeight.BOLD, size=14),
                    ft.Row([
                        ft.OutlinedButton(
                            f"Pay from Wallet (${wallet['balance']:.2f})",
                            icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                            disabled=wallet['balance'] < total,
                            on_click=lambda _: complete_payment("wallet")
                        ),
                        ft.OutlinedButton(
                            "Walk-in Cash Tender",
                            icon=ft.Icons.ATTACH_MONEY,
                            on_click=lambda _: complete_payment("cash")
                        ),
                    ], spacing=10)
                ], spacing=12, scroll=ft.ScrollMode.AUTO),
                width=460,
                height=420
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog())
            ]
        )

        self.app_page.show_dialog(checkout_dialog)

    def show_receipt(self, tx_id, method, items, subtotal, tax, total, pay_ref):
        item_rows = []
        for it in items:
            item_rows.append(
                ft.Row([
                    ft.Text(f"{it['qty']}x {it['name']}", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Text(f"${it['subtotal']:.2f}", size=12, weight=ft.FontWeight.W_600)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        receipt_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.GREEN_700),
                ft.Text("Digital Receipt", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(database.get_setting("store_name", "Fintech Store"), size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Official Order Confirmation", size=11, color=ft.Colors.GREY_600),
                            ft.Text(f"Receipt ID: {tx_id}", size=12, weight=ft.FontWeight.W_500),
                            ft.Text(f"Payment Method: {method.upper()} ({pay_ref})", size=11, color=ft.Colors.GREY_700),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.only(bottom=8)
                    ),
                    ft.Divider(height=10),
                    ft.Column(item_rows, spacing=4),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Subtotal:", size=12), ft.Text(f"${subtotal:.2f}", size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Tax (8%):", size=12), ft.Text(f"${tax:.2f}", size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Total Paid:", size=14, weight=ft.FontWeight.BOLD), ft.Text(f"${total:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.Container(
                        content=ft.Text("✓ Payment Approved & Recorded in Database", size=11, color=ft.Colors.GREEN_800, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=ft.Padding.all(8),
                        border_radius=ft.BorderRadius.all(6),
                        alignment=ft.Alignment.CENTER
                    )
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                width=360,
                height=380
            ),
            actions=[
                ft.FilledButton("Done", style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE), on_click=lambda _: self.app_page.pop_dialog())
            ]
        )
        self.app_page.show_dialog(receipt_dialog)

    def show_snack(self, msg: str):
        self.app_page.show_dialog(ft.SnackBar(ft.Text(msg)))

    def refresh(self):
        self.load_products()
        self.refresh_cart()
