import flet as ft
import database
from paypal_service import paypal_service

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, on_settings_changed=None):
        super().__init__(expand=True)
        self.app_page = page
        self.on_settings_changed = on_settings_changed
        self.padding = ft.Padding.all(20)

        # Settings controls
        self.paypal_mode_dropdown = ft.Dropdown(
            label="PayPal Environment Mode",
            value="sandbox",
            options=[
                ft.DropdownOption("sandbox", "Sandbox (Testing & Developer)"),
                ft.DropdownOption("live", "Live (Production Payments)")
            ],
            border_radius=ft.BorderRadius.all(10)
        )
        self.client_id_field = ft.TextField(
            label="PayPal REST API Client ID",
            hint_text="e.g. A21AA...",
            password=True,
            can_reveal_password=True,
            border_radius=ft.BorderRadius.all(10)
        )
        self.client_secret_field = ft.TextField(
            label="PayPal REST API Client Secret",
            hint_text="e.g. EK...",
            password=True,
            can_reveal_password=True,
            border_radius=ft.BorderRadius.all(10)
        )
        self.simulation_switch = ft.Switch(
            label="Enable Demo / Simulation Sandbox Fallback",
            value=True
        )
        self.test_status_text = ft.Text("", size=12)

        self.store_name_field = ft.TextField(label="Store / Business Name", border_radius=ft.BorderRadius.all(10))
        self.tax_rate_field = ft.TextField(label="Default Tax Rate (%)", border_radius=ft.BorderRadius.all(10), keyboard_type=ft.KeyboardType.NUMBER)
        self.currency_dropdown = ft.Dropdown(
            label="Default Currency",
            value="USD",
            options=[
                ft.DropdownOption("USD", "USD ($) - US Dollar"),
                ft.DropdownOption("EUR", "EUR (€) - Euro"),
                ft.DropdownOption("GBP", "GBP (£) - British Pound")
            ],
            border_radius=ft.BorderRadius.all(10)
        )

        self.content = self.build_ui()
        self.load_values()

    def build_ui(self):
        # Section 1: PayPal API Settings
        paypal_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PAYMENTS, color="#003087"),
                    ft.Text("PayPal Developer & API Credentials", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Text("Configure your PayPal Developer REST API credentials or keep Demo Simulation enabled for zero-setup local testing.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=10),
                self.paypal_mode_dropdown,
                self.client_id_field,
                self.client_secret_field,
                ft.Row([
                    self.simulation_switch,
                    ft.Text("(Instant mock payments without requiring real keys)", size=11, color=ft.Colors.GREY_600)
                ], spacing=6),
                self.test_status_text,
                ft.Row([
                    ft.FilledButton(
                        "Test API Connection",
                        icon=ft.Icons.NETWORK_CHECK,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                        on_click=self.test_paypal_connection
                    ),
                    ft.FilledButton(
                        "Save PayPal Settings",
                        icon=ft.Icons.SAVE,
                        style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
                        on_click=self.save_paypal_settings
                    )
                ], spacing=10)
            ], spacing=12),
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.all(14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        # Section 2: Store Profile Settings
        store_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STOREFRONT, color="#003087"),
                    ft.Text("Store & Terminal Profile", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Text("Customize your merchant identity for invoices and checkout receipts.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=10),
                self.store_name_field,
                ft.Row([self.tax_rate_field, self.currency_dropdown], spacing=12),
                ft.FilledButton(
                    "Save Store Profile",
                    icon=ft.Icons.SAVE,
                    style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
                    on_click=self.save_store_settings
                )
            ], spacing=12),
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.all(14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        # Section 3: Data & Reset
        data_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STORAGE, color=ft.Colors.ORANGE_800),
                    ft.Text("Database Management", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Text("Local SQLite database storing wallet balances, catalog, receipts, and settings.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=10),
                ft.Row([
                    ft.OutlinedButton(
                        "Reset to Demo Data",
                        icon=ft.Icons.RESTORE,
                        icon_color=ft.Colors.RED_400,
                        on_click=self.reset_data
                    )
                ])
            ], spacing=12),
            padding=ft.Padding.all(20),
            border_radius=ft.BorderRadius.all(14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        return ft.ListView([
            ft.Text("Application Settings & PayPal Integration", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            paypal_card,
            ft.Container(height=16),
            store_card,
            ft.Container(height=16),
            data_card
        ], spacing=0, expand=True)

    def safe_update(self):
        try:
            self.update()
        except:
            pass

    def load_values(self):
        settings = database.get_all_settings()
        self.paypal_mode_dropdown.value = settings.get("paypal_mode", "sandbox")
        self.client_id_field.value = settings.get("paypal_client_id", "")
        self.client_secret_field.value = settings.get("paypal_client_secret", "")
        self.simulation_switch.value = settings.get("simulation_mode", "true").lower() == "true"

        self.store_name_field.value = settings.get("store_name", "NovaTech Retail & Fintech")
        self.tax_rate_field.value = settings.get("tax_rate", "8.0")
        self.currency_dropdown.value = settings.get("currency", "USD")
        self.safe_update()

    def test_paypal_connection(self, _):
        client_id = self.client_id_field.value.strip()
        client_secret = self.client_secret_field.value.strip()
        mode = self.paypal_mode_dropdown.value or "sandbox"

        if not client_id or not client_secret:
            self.test_status_text.value = "⚠️ Please enter both Client ID and Client Secret to test connection."
            self.test_status_text.color = ft.Colors.ORANGE_800
            self.safe_update()
            return

        self.test_status_text.value = "Connecting to PayPal OAuth server..."
        self.test_status_text.color = ft.Colors.BLUE_700
        self.safe_update()

        res = paypal_service.test_connection(client_id, client_secret, mode)
        if res["success"]:
            self.test_status_text.value = f"✓ {res['message']}"
            self.test_status_text.color = ft.Colors.GREEN_700
        else:
            self.test_status_text.value = f"✗ {res['message']}"
            self.test_status_text.color = ft.Colors.RED_700
        self.safe_update()

    def save_paypal_settings(self, _):
        database.set_setting("paypal_mode", self.paypal_mode_dropdown.value or "sandbox")
        database.set_setting("paypal_client_id", self.client_id_field.value.strip())
        database.set_setting("paypal_client_secret", self.client_secret_field.value.strip())
        database.set_setting("simulation_mode", "true" if self.simulation_switch.value else "false")

        if self.on_settings_changed:
            self.on_settings_changed()
        self.app_page.show_dialog(ft.SnackBar(ft.Text("✓ PayPal settings saved successfully!")))

    def save_store_settings(self, _):
        store_name = self.store_name_field.value.strip()
        tax_str = self.tax_rate_field.value.strip()
        currency = self.currency_dropdown.value or "USD"

        if not store_name:
            self.app_page.show_dialog(ft.SnackBar(ft.Text("Store name cannot be empty.")))
            return
        try:
            float(tax_str)
        except ValueError:
            self.app_page.show_dialog(ft.SnackBar(ft.Text("Tax rate must be a valid number.")))
            return

        database.set_setting("store_name", store_name)
        database.set_setting("tax_rate", tax_str)
        database.set_setting("currency", currency)

        if self.on_settings_changed:
            self.on_settings_changed()
        self.app_page.show_dialog(ft.SnackBar(ft.Text("✓ Store settings updated!")))

    def reset_data(self, _):
        database.init_db()
        self.load_values()
        if self.on_settings_changed:
            self.on_settings_changed()
        self.app_page.show_dialog(ft.SnackBar(ft.Text("✓ Demo database reloaded with fresh sample data.")))

    def refresh(self):
        self.load_values()
