import sys
import flet as ft
import database
from paypal_service import paypal_service

from views.dashboard_view import DashboardView
from views.pos_view import PosView
from views.wallet_view import WalletView
from views.transactions_view import TransactionsView
from views.inventory_view import InventoryView
from views.settings_view import SettingsView

def main(page: ft.Page):
    # Initialize database tables and seed sample data
    database.init_db()

    page.title = "PayPal Point of Sale & Fintech Hub"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # TopBar Widgets
    store_title_text = ft.Text(database.get_setting("store_name", "NovaTech Retail & Fintech"), size=16, weight=ft.FontWeight.BOLD)
    
    mode_badge_text = ft.Text("", size=11, weight=ft.FontWeight.BOLD)
    mode_badge_container = ft.Container(
        content=mode_badge_text,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=ft.border_radius.all(12),
    )

    balance_pill_text = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    balance_pill = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.WHITE, size=16),
            balance_pill_text
        ], spacing=6),
        bgcolor="#003087",
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=ft.border_radius.all(20),
        on_click=lambda _: navigate_to("wallet")
    )

    def update_header():
        wallet = database.get_wallet()
        balance_pill_text.value = f"${wallet['balance']:,.2f}"

        cfg = paypal_service.get_config()
        if cfg["simulation_mode"]:
            mode_badge_text.value = "⚡ PayPal Simulation"
            mode_badge_text.color = ft.Colors.BLUE_900
            mode_badge_container.bgcolor = ft.Colors.BLUE_100
        elif cfg["mode"] == "live":
            mode_badge_text.value = "🟢 PayPal Live Production"
            mode_badge_text.color = ft.Colors.GREEN_900
            mode_badge_container.bgcolor = ft.Colors.GREEN_100
        else:
            mode_badge_text.value = "🌐 PayPal Sandbox Active"
            mode_badge_text.color = ft.Colors.CYAN_900
            mode_badge_container.bgcolor = ft.Colors.CYAN_100

        store_title_text.value = database.get_setting("store_name", "NovaTech Retail & Fintech")
        page.update()

    def toggle_theme(_):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon = ft.Icons.LIGHT_MODE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon = ft.Icons.DARK_MODE
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        tooltip="Toggle Dark/Light Mode",
        on_click=toggle_theme
    )

    app_bar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PAYMENTS_ROUNDED, color=ft.Colors.WHITE, size=22),
                    padding=ft.padding.all(8),
                    border_radius=ft.border_radius.all(10),
                    bgcolor="#003087"
                ),
                ft.Column([
                    store_title_text,
                    ft.Text("PayPal Cross-Platform POS & Wallet Manager", size=11, color=ft.Colors.GREY_600)
                ], spacing=2)
            ], spacing=10),
            ft.Row([
                mode_badge_container,
                balance_pill,
                theme_btn
            ], spacing=12)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.SURFACE
    )

    # Content Container
    content_area = ft.Container(expand=True)

    # Views Registry
    views = {}

    def on_tx_sync():
        update_header()
        if "dashboard" in views:
            views["dashboard"].refresh()
        if "transactions" in views:
            views["transactions"].refresh()
        if "wallet" in views:
            views["wallet"].refresh()
        if "pos" in views:
            views["pos"].refresh()

    def on_catalog_sync():
        if "pos" in views:
            views["pos"].refresh()
        if "inventory" in views:
            views["inventory"].refresh()

    def on_settings_sync():
        update_header()
        if "dashboard" in views:
            views["dashboard"].refresh()

    views["dashboard"] = DashboardView(page, navigate_to=lambda target: navigate_to(target))
    views["pos"] = PosView(page, on_transaction_completed=on_tx_sync)
    views["wallet"] = WalletView(page, on_transaction_completed=on_tx_sync)
    views["transactions"] = TransactionsView(page)
    views["inventory"] = InventoryView(page, on_catalog_updated=on_catalog_sync)
    views["settings"] = SettingsView(page, on_settings_changed=on_settings_sync)

    nav_index_map = ["dashboard", "pos", "wallet", "transactions", "inventory", "settings"]

    def set_active_view(view_key: str):
        if view_key in views:
            content_area.content = views[view_key]
            views[view_key].refresh()
            page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=72,
        min_extended_width=180,
        leading=ft.Container(height=10),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.POINT_OF_SALE_OUTLINED,
                selected_icon=ft.Icons.POINT_OF_SALE,
                label="POS Checkout"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                selected_icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                label="Wallet & P2P"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                selected_icon=ft.Icons.RECEIPT_LONG,
                label="Ledger & Receipts"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Catalog"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings"
            ),
        ],
        on_change=lambda e: on_nav_change(e.control.selected_index)
    )

    def on_nav_change(index: int):
        rail.selected_index = index
        key = nav_index_map[index]
        set_active_view(key)

    def navigate_to(target: str):
        if target == "wallet_send":
            rail.selected_index = 2
            set_active_view("wallet")
        elif target == "wallet_receive":
            rail.selected_index = 2
            set_active_view("wallet")
        elif target in nav_index_map:
            idx = nav_index_map.index(target)
            rail.selected_index = idx
            set_active_view(target)

    # Initial view load
    content_area.content = views["dashboard"]
    update_header()

    main_layout = ft.Column([
        app_bar,
        ft.Row([
            rail,
            ft.VerticalDivider(width=1),
            content_area
        ], expand=True, spacing=0)
    ], expand=True, spacing=0)

    page.add(main_layout)

if __name__ == "__main__":
    # Determine view mode: Web Browser or Native Desktop Window
    view_mode = ft.AppView.FLET_APP
    if "--web" in sys.argv:
        view_mode = ft.AppView.WEB_BROWSER
    
    ft.run(main, view=view_mode)
