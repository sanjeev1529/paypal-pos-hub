import flet as ft
import database

def get_icon(name: str):
    clean = (name or "SHOPPING_BAG").replace("-", "_").upper()
    return getattr(ft.Icons, clean, ft.Icons.SHOPPING_BAG)

class InventoryView(ft.Container):
    def __init__(self, page: ft.Page, on_catalog_updated=None):
        super().__init__(expand=True)
        self.app_page = page
        self.on_catalog_updated = on_catalog_updated
        self.search_term = ""
        self.padding = ft.Padding.all(20)

        self.products_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.content = self.build_ui()
        self.load_products()

    def build_ui(self):
        search_box = ft.TextField(
            hint_text="Search product by name, SKU, or category...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            border_radius=ft.BorderRadius.all(10),
            expand=True,
            on_change=self.on_search_change
        )

        add_btn = ft.FilledButton(
            "Add Product",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
            on_click=lambda _: self.open_product_modal()
        )

        header = ft.Row([
            ft.Text("Catalog & Stock Management", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            add_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Column([
            header,
            search_box,
            ft.Divider(height=10),
            self.products_col
        ], spacing=12, expand=True)

    def safe_update(self):
        try:
            self.update()
        except:
            pass

    def on_search_change(self, e):
        self.search_term = e.control.value
        self.load_products()

    def load_products(self):
        self.products_col.controls.clear()
        prods = database.get_products(search=self.search_term)

        if not prods:
            self.products_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No products found in inventory.", color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.all(40)
                )
            )
        else:
            for p in prods:
                stock_alert = p["stock"] < 10
                stock_color = ft.Colors.RED_700 if stock_alert else ft.Colors.GREEN_700

                row = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(get_icon(p["icon"]), color="#003087", size=24),
                                padding=ft.Padding.all(10),
                                border_radius=ft.BorderRadius.all(10),
                                bgcolor=ft.Colors.BLUE_50
                            ),
                            ft.Column([
                                ft.Row([
                                    ft.Text(p["name"], size=14, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        content=ft.Text(p["category"], size=10, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_800),
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                        border_radius=ft.BorderRadius.all(4),
                                        bgcolor=ft.Colors.BLUE_50
                                    )
                                ], spacing=8),
                                ft.Text(f"SKU: {p['sku']} • {p['description'] or 'No description'}", size=12, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ], spacing=2)
                        ], spacing=12, expand=True),
                        ft.Row([
                            ft.Column([
                                ft.Text(f"${p['price']:.2f}", size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{p['stock']} in stock", size=12, weight=ft.FontWeight.W_600, color=stock_color),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                            ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, tooltip="Edit", on_click=lambda _, prod=p: self.open_product_modal(prod)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=ft.Colors.RED_400, tooltip="Delete", on_click=lambda _, pid=p["id"]: self.delete_product(pid))
                        ], spacing=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    border_radius=ft.BorderRadius.all(12),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                )
                self.products_col.controls.append(row)

        self.safe_update()

    def open_product_modal(self, prod: dict = None):
        is_edit = prod is not None
        title = "Edit Product" if is_edit else "Add New Product"

        name_f = ft.TextField(label="Product Name", value=prod["name"] if is_edit else "", border_radius=ft.BorderRadius.all(8))
        sku_f = ft.TextField(label="SKU / Barcode", value=prod["sku"] if is_edit else f"PROD-{len(database.get_products())+1:03d}", border_radius=ft.BorderRadius.all(8))
        cat_f = ft.Dropdown(
            label="Category",
            value=prod["category"] if is_edit else "Electronics",
            options=[
                ft.DropdownOption("Electronics", "Electronics"),
                ft.DropdownOption("Beverages", "Beverages"),
                ft.DropdownOption("Accessories", "Accessories"),
                ft.DropdownOption("Services", "Services"),
                ft.DropdownOption("General", "General")
            ],
            border_radius=ft.BorderRadius.all(8)
        )
        price_f = ft.TextField(label="Price ($)", value=f"{prod['price']:.2f}" if is_edit else "19.99", border_radius=ft.BorderRadius.all(8), keyboard_type=ft.KeyboardType.NUMBER)
        stock_f = ft.TextField(label="Stock Quantity", value=str(prod["stock"]) if is_edit else "50", border_radius=ft.BorderRadius.all(8), keyboard_type=ft.KeyboardType.NUMBER)
        desc_f = ft.TextField(label="Description", value=prod["description"] if is_edit else "", border_radius=ft.BorderRadius.all(8), multiline=True, max_lines=2)

        def save_product(_):
            name = name_f.value.strip()
            sku = sku_f.value.strip()
            cat = cat_f.value or "General"
            if not name or not sku:
                self.app_page.show_dialog(ft.SnackBar(ft.Text("Name and SKU are required.")))
                return
            try:
                price = float(price_f.value.strip())
                stock = int(stock_f.value.strip())
            except ValueError:
                self.app_page.show_dialog(ft.SnackBar(ft.Text("Please enter valid price and stock numbers.")))
                return

            if is_edit:
                database.update_product(prod["id"], name, sku, cat, price, stock, prod.get("icon", "shopping_bag"), desc_f.value.strip())
            else:
                database.add_product(name, sku, cat, price, stock, "shopping_bag", desc_f.value.strip())

            self.app_page.pop_dialog()
            self.load_products()
            if self.on_catalog_updated:
                self.on_catalog_updated()
            self.app_page.show_dialog(ft.SnackBar(ft.Text(f"✓ Product '{name}' saved successfully!")))

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2, color="#003087"),
                ft.Text(title, weight=ft.FontWeight.BOLD, size=18)
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    name_f,
                    sku_f,
                    cat_f,
                    ft.Row([price_f, stock_f], spacing=10),
                    desc_f
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=420,
                height=360
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.app_page.pop_dialog()),
                ft.FilledButton("Save", style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE), on_click=save_product)
            ]
        )
        self.app_page.show_dialog(dlg)

    def delete_product(self, pid: int):
        database.delete_product(pid)
        self.load_products()
        if self.on_catalog_updated:
            self.on_catalog_updated()
        self.app_page.show_dialog(ft.SnackBar(ft.Text("Product removed from inventory.")))

    def refresh(self):
        self.load_products()
