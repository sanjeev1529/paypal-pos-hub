import flet as ft
import database

class DashboardView(ft.Container):
    def __init__(self, page: ft.Page, navigate_to):
        super().__init__(expand=True)
        self.app_page = page
        self.navigate_to = navigate_to
        self.padding = ft.Padding.all(24)
        self.content = self.build_ui()

    def build_ui(self):
        summary = database.get_dashboard_summary()
        currency_sym = "$"

        # Action buttons with interactive hover scale
        def create_action_btn(text, icon, bg, fg, click_handler):
            btn_box = ft.Container(
                content=ft.FilledButton(
                    text,
                    icon=icon,
                    style=ft.ButtonStyle(bgcolor=bg, color=fg),
                    on_click=click_handler
                ),
                animate_scale=ft.Animation(160, "easeOut") if hasattr(ft, "Animation") else 160,
                on_hover=lambda e: (
                    setattr(e.control, "scale", 1.05 if str(getattr(e, "data", "")).lower() == "true" else 1.0),
                    e.control.update()
                )
            )
            return btn_box

        # Balance Card (PayPal Blue Gradient look with tactile hover depth)
        balance_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("TOTAL WALLET BALANCE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_70),
                        ft.Text(f"{currency_sym}{summary['balance']:,.2f}", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ], spacing=4),
                    ft.Container(
                        content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.WHITE, size=32),
                        padding=ft.Padding.all(12),
                        border_radius=ft.BorderRadius.all(12),
                        bgcolor=ft.Colors.WHITE_24,
                        animate_scale=ft.Animation(200, "easeOut") if hasattr(ft, "Animation") else 200,
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ft.Colors.WHITE_24, height=20),
                ft.Row([
                    create_action_btn("New Sale (POS)", ft.Icons.POINT_OF_SALE, ft.Colors.WHITE, "#003087", lambda _: self.navigate_to("pos")),
                    create_action_btn("Send Money", ft.Icons.SEND, ft.Colors.WHITE_24, ft.Colors.WHITE, lambda _: self.navigate_to("wallet_send")),
                    create_action_btn("Request / QR", ft.Icons.QR_CODE, ft.Colors.WHITE_24, ft.Colors.WHITE, lambda _: self.navigate_to("wallet_receive")),
                ], spacing=10, wrap=True)
            ]),
            padding=ft.Padding.all(24),
            border_radius=ft.BorderRadius.all(16),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#003087", "#0079C1"]
            ),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK_12, offset=ft.Offset(0, 4)),
            animate_scale=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
            animate=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
        )

        def on_balance_card_hover(e):
            is_hover = str(getattr(e, "data", "")).lower() == "true"
            balance_card.scale = 1.01 if is_hover else 1.0
            balance_card.shadow = ft.BoxShadow(blur_radius=22, color=ft.Colors.BLACK_26, offset=ft.Offset(0, 6)) if is_hover else ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK_12, offset=ft.Offset(0, 4))
            try:
                balance_card.update()
            except Exception:
                pass

        balance_card.on_hover = on_balance_card_hover

        # Metric Cards Row
        metric_sales = self.build_metric_card(
            title="Today's Sales",
            value=f"{currency_sym}{summary['total_sales']:,.2f}",
            subtitle=f"{summary['sales_count']} POS / PayPal sales",
            icon=ft.Icons.TRENDING_UP,
            icon_color=ft.Colors.GREEN_400,
            bg_color=ft.Colors.GREEN_50
        )

        metric_spent = self.build_metric_card(
            title="Total Outflow",
            value=f"{currency_sym}{summary['total_sent']:,.2f}",
            subtitle="P2P Transfers & Payouts",
            icon=ft.Icons.CALL_MADE,
            icon_color=ft.Colors.ORANGE_400,
            bg_color=ft.Colors.ORANGE_50
        )

        metric_inventory = self.build_metric_card(
            title="Catalog Status",
            value=f"{summary['low_stock_count']} Low Stock",
            subtitle="Products needing restock",
            icon=ft.Icons.INVENTORY_2,
            icon_color=ft.Colors.BLUE_400 if summary['low_stock_count'] == 0 else ft.Colors.RED_400,
            bg_color=ft.Colors.BLUE_50 if summary['low_stock_count'] == 0 else ft.Colors.RED_50
        )

        metrics_row = ft.Row([
            ft.Container(content=metric_sales, expand=True),
            ft.Container(content=metric_spent, expand=True),
            ft.Container(content=metric_inventory, expand=True),
        ], spacing=16)

        # Recent Transactions Header & List
        recent_txs = database.get_transactions(limit=6)
        tx_rows = []
        if recent_txs:
            for tx in recent_txs:
                is_incoming = tx["type"] in ("pos_sale", "transfer_received", "wallet_deposit")
                amt_str = f"+{currency_sym}{tx['amount']:,.2f}" if is_incoming else f"-{currency_sym}{tx['amount']:,.2f}"
                amt_color = ft.Colors.GREEN_700 if is_incoming else ft.Colors.RED_700
                icon_name = ft.Icons.POINT_OF_SALE if tx["type"] == "pos_sale" else (
                    ft.Icons.CALL_RECEIVED if tx["type"] == "transfer_received" else (
                        ft.Icons.ACCOUNT_BALANCE if tx["type"] == "wallet_deposit" else ft.Icons.SEND
                    )
                )

                def make_tx_hover(row_ref):
                    def on_hover(e):
                        is_hover = str(getattr(e, "data", "")).lower() == "true"
                        row_ref.offset = ft.Offset(0.012, 0) if is_hover else ft.Offset(0, 0)
                        row_ref.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH if is_hover else ft.Colors.SURFACE_CONTAINER_LOW
                        row_ref.border = ft.Border.all(1, ft.Colors.BLUE_200) if is_hover else None
                        try:
                            row_ref.update()
                        except Exception:
                            pass
                    return on_hover

                tx_item = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(icon_name, color="#003087", size=20),
                                padding=ft.Padding.all(10),
                                border_radius=ft.BorderRadius.all(10),
                                bgcolor=ft.Colors.BLUE_50
                            ),
                            ft.Column([
                                ft.Text(tx["reference_note"] or tx["counterparty"] or "Transaction", weight=ft.FontWeight.W_600, size=14),
                                ft.Text(f"{tx['timestamp']} • {tx['paypal_order_id'] or tx['id']}", size=12, color=ft.Colors.GREY_600),
                            ], spacing=2)
                        ], spacing=12),
                        ft.Column([
                            ft.Text(amt_str, size=15, weight=ft.FontWeight.BOLD, color=amt_color),
                            ft.Container(
                                content=ft.Text(tx["status"].upper(), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800 if tx["status"] == "completed" else ft.Colors.ORANGE_800),
                                bgcolor=ft.Colors.GREEN_100 if tx["status"] == "completed" else ft.Colors.ORANGE_100,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                border_radius=ft.BorderRadius.all(4)
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                    border_radius=ft.BorderRadius.all(8),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    animate_offset=ft.Animation(160, "easeOut") if hasattr(ft, "Animation") else 160,
                    animate=ft.Animation(160, "easeOut") if hasattr(ft, "Animation") else 160,
                )
                tx_item.on_hover = make_tx_hover(tx_item)
                tx_rows.append(tx_item)
        else:
            tx_rows.append(ft.Text("No transactions recorded yet.", italic=True, color=ft.Colors.GREY_500))

        recent_tx_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Recent Transactions", size=18, weight=ft.FontWeight.BOLD),
                    ft.TextButton("View All", icon=ft.Icons.ARROW_FORWARD, on_click=lambda _: self.navigate_to("transactions"))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10),
                ft.Column(tx_rows, spacing=8)
            ]),
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.all(16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            animate=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
        )

        return ft.ListView([
            balance_card,
            ft.Container(height=16),
            metrics_row,
            ft.Container(height=24),
            recent_tx_card
        ], spacing=0, expand=True)

    def build_metric_card(self, title, value, subtitle, icon, icon_color, bg_color):
        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Container(
                        content=ft.Icon(icon, color=icon_color, size=20),
                        padding=ft.Padding.all(8),
                        border_radius=ft.BorderRadius.all(8),
                        bgcolor=bg_color,
                        animate_scale=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=12, color=ft.Colors.GREY_600)
            ], spacing=6),
            padding=ft.Padding.all(18),
            border_radius=ft.BorderRadius.all(12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            animate_scale=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
            animate=ft.Animation(180, "easeOut") if hasattr(ft, "Animation") else 180,
        )

        def on_metric_hover(e):
            is_hover = str(getattr(e, "data", "")).lower() == "true"
            card.scale = 1.025 if is_hover else 1.0
            card.border = ft.Border.all(1.5, "#0070BA") if is_hover else ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
            card.shadow = ft.BoxShadow(blur_radius=16, color=ft.Colors.BLACK_12, offset=ft.Offset(0, 4)) if is_hover else None
            try:
                card.update()
            except Exception:
                pass

        card.on_hover = on_metric_hover
        return card

    def safe_update(self):
        try:
            self.update()
        except:
            pass

    def refresh(self):
        self.content = self.build_ui()
        self.safe_update()
