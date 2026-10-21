import csv
import json
import os
import flet as ft
import database
from config import BASE_DIR

class TransactionsView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.app_page = page
        self.selected_filter = "All"
        self.search_term = ""
        self.padding = ft.Padding.all(20)

        self.filter_chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.tx_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        self.content = self.build_ui()
        self.load_transactions()

    def build_ui(self):
        filters = [
            ("All", "All"),
            ("POS Sales", "pos_sale"),
            ("Money Sent", "transfer_sent"),
            ("Money Received", "transfer_received"),
            ("Deposits", "wallet_deposit"),
            ("Withdrawals", "wallet_withdraw")
        ]

        self.filter_chips_row.controls.clear()
        for label, val in filters:
            is_sel = val == self.selected_filter
            self.filter_chips_row.controls.append(
                ft.FilledTonalButton(
                    label,
                    style=ft.ButtonStyle(
                        bgcolor="#003087" if is_sel else ft.Colors.SURFACE_CONTAINER_HIGH,
                        color=ft.Colors.WHITE if is_sel else ft.Colors.ON_SURFACE
                    ),
                    on_click=lambda _, v=val: self.select_filter(v)
                )
            )

        search_box = ft.TextField(
            hint_text="Search by Order ID, email, note, or ID...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            border_radius=ft.BorderRadius.all(10),
            expand=True,
            on_change=self.on_search_change
        )

        export_btn = ft.OutlinedButton(
            "Export CSV",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.export_csv
        )

        header = ft.Row([
            ft.Text("Transaction Ledger & Receipts", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            export_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        controls_row = ft.Row([search_box], spacing=12)

        return ft.Column([
            header,
            controls_row,
            self.filter_chips_row,
            ft.Divider(height=10),
            self.tx_list_col
        ], spacing=12, expand=True)

    def safe_update(self):
        try:
            self.update()
        except:
            pass

    def select_filter(self, val: str):
        self.selected_filter = val
        self.content = self.build_ui()
        self.load_transactions()
        self.safe_update()

    def on_search_change(self, e):
        self.search_term = e.control.value
        self.load_transactions()

    def load_transactions(self):
        self.tx_list_col.controls.clear()
        filter_type = self.selected_filter if self.selected_filter != "All" else None
        txs = database.get_transactions(limit=150, filter_type=filter_type, search=self.search_term)

        if not txs:
            self.tx_list_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=50, color=ft.Colors.GREY_400),
                        ft.Text("No transactions match your search.", color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.all(40)
                )
            )
        else:
            for tx in txs:
                is_incoming = tx["type"] in ("pos_sale", "transfer_received", "wallet_deposit")
                amt_str = f"+${tx['amount']:,.2f}" if is_incoming else f"-${tx['amount']:,.2f}"
                amt_color = ft.Colors.GREEN_700 if is_incoming else ft.Colors.RED_700

                type_label = {
                    "pos_sale": "POS Checkout Sale",
                    "transfer_sent": "Money Sent (P2P)",
                    "transfer_received": "Money Received",
                    "wallet_deposit": "Wallet Deposit",
                    "wallet_withdraw": "Bank Withdrawal"
                }.get(tx["type"], tx["type"].upper())

                icon_name = {
                    "pos_sale": ft.Icons.POINT_OF_SALE,
                    "transfer_sent": ft.Icons.SEND,
                    "transfer_received": ft.Icons.CALL_RECEIVED,
                    "wallet_deposit": ft.Icons.ADD_CARD,
                    "wallet_withdraw": ft.Icons.ACCOUNT_BALANCE
                }.get(tx["type"], ft.Icons.PAYMENTS)

                item = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(icon_name, color="#003087", size=22),
                                padding=ft.Padding.all(10),
                                border_radius=ft.BorderRadius.all(10),
                                bgcolor=ft.Colors.BLUE_50
                            ),
                            ft.Column([
                                ft.Row([
                                    ft.Text(type_label, weight=ft.FontWeight.BOLD, size=14),
                                    ft.Container(
                                        content=ft.Text(tx["id"], size=10, color=ft.Colors.GREY_700),
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                        border_radius=ft.BorderRadius.all(4),
                                        bgcolor=ft.Colors.GREY_100
                                    )
                                ], spacing=8),
                                ft.Text(tx["reference_note"] or tx["counterparty"] or "No notes", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{tx['timestamp']} • Ref: {tx['paypal_order_id'] or 'N/A'}", size=11, color=ft.Colors.GREY_600)
                            ], spacing=2)
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Column([
                                ft.Text(amt_str, size=16, weight=ft.FontWeight.BOLD, color=amt_color),
                                ft.Container(
                                    content=ft.Text(tx["status"].upper(), size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                                    bgcolor=ft.Colors.GREEN_50,
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=ft.BorderRadius.all(4)
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                            ft.IconButton(
                                ft.Icons.INFO_OUTLINE,
                                icon_size=20,
                                tooltip="View Receipt & Breakdown",
                                on_click=lambda _, t=tx: self.show_tx_details(t)
                            )
                        ], spacing=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    border_radius=ft.BorderRadius.all(12),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                )
                self.tx_list_col.controls.append(item)

        self.safe_update()

    def show_tx_details(self, tx: dict):
        items = []
        try:
            items = json.loads(tx.get("items_json") or "[]")
        except:
            items = []

        items_col = ft.Column(spacing=4)
        if items:
            items_col.controls.append(ft.Text("Order Line Items:", weight=ft.FontWeight.BOLD, size=12))
            for it in items:
                items_col.controls.append(
                    ft.Row([
                        ft.Text(f"{it.get('qty', 1)}x {it.get('name', 'Product')}", size=12),
                        ft.Text(f"${it.get('subtotal', it.get('price', 0)):.2f}", size=12, weight=ft.FontWeight.W_500)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            items_col.controls.append(ft.Divider(height=10))

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT, color="#003087"),
                ft.Text("Transaction Details", weight=ft.FontWeight.BOLD, size=18)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("Transaction ID:", color=ft.Colors.GREY_600), ft.Text(tx["id"], weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Type:", color=ft.Colors.GREY_600), ft.Text(tx["type"].upper(), weight=ft.FontWeight.W_600)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Timestamp:", color=ft.Colors.GREY_600), ft.Text(tx["timestamp"])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Counterparty:", color=ft.Colors.GREY_600), ft.Text(tx["counterparty"] or "N/A")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("PayPal / Order Ref:", color=ft.Colors.GREY_600), ft.Text(tx["paypal_order_id"] or "N/A", weight=ft.FontWeight.W_500)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Note:", color=ft.Colors.GREY_600), ft.Text(tx["reference_note"] or "N/A", max_lines=2)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    items_col,
                    ft.Row([ft.Text("Gross Amount:", size=13), ft.Text(f"${tx['amount']:.2f}", size=13, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Estimated Fee:", size=12, color=ft.Colors.GREY_600), ft.Text(f"${tx['fee']:.2f}", size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Net Impact:", size=14, weight=ft.FontWeight.BOLD), ft.Text(f"${tx['net']:.2f}", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800 if tx['net'] >= 0 else ft.Colors.RED_800)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=8, scroll=ft.ScrollMode.AUTO),
                width=400,
                height=340
            ),
            actions=[
                ft.FilledButton("Close", style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE), on_click=lambda _: self.app_page.pop_dialog())
            ]
        )
        self.app_page.show_dialog(dlg)

    def export_csv(self, _):
        txs = database.get_transactions(limit=1000)
        export_path = BASE_DIR / "transactions_export.csv"
        try:
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Type", "Amount", "Currency", "Fee", "Net", "Status", "Counterparty", "PayPal_Order_ID", "Reference_Note", "Timestamp"])
                for tx in txs:
                    writer.writerow([tx["id"], tx["type"], tx["amount"], tx["currency"], tx["fee"], tx["net"], tx["status"], tx["counterparty"], tx["paypal_order_id"], tx["reference_note"], tx["timestamp"]])
            self.app_page.show_dialog(ft.SnackBar(ft.Text(f"✓ Exported {len(txs)} transactions to {export_path.name}")))
        except Exception as e:
            self.app_page.show_dialog(ft.SnackBar(ft.Text(f"Export failed: {str(e)}")))

    def refresh(self):
        self.load_transactions()
