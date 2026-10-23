import sys
import flet as ft
import database

from views.inventory_view import InventoryView
from views.room_designer_view import RoomDesignerView

DEEP_GREEN = "#234A3D"
SOFT_GREEN = "#E8F0E9"
WARM_WHITE = "#FBFAF7"


class HomeDecorHomeView(ft.Container):
    def __init__(self, page, navigate_to):
        super().__init__(expand=True, padding=ft.Padding.all(24))
        self.navigate_to = navigate_to
        self.product_grid = ft.GridView(expand=True, runs_count=3, max_extent=240,
                                        child_aspect_ratio=1.55, spacing=12, run_spacing=12)
        self.content = self.build_ui()
        self.refresh()

    def build_ui(self):
        hero = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Make room for home.", size=32, weight=ft.FontWeight.BOLD, color=DEEP_GREEN),
                    ft.Text("Thoughtful furniture and decor, imagined in your own space.",
                            size=14, color=ft.Colors.GREY_700),
                    ft.FilledButton("Visualize your room", icon=ft.Icons.AUTO_AWESOME,
                                    style=ft.ButtonStyle(bgcolor=DEEP_GREEN, color=ft.Colors.WHITE),
                                    on_click=lambda _: self.navigate_to("designer"))
                ], spacing=14, expand=True),
                ft.Container(content=ft.Icon(ft.Icons.CHAIR_ALT, size=72, color=DEEP_GREEN),
                             padding=28, bgcolor="#DCE8DD", border_radius=80)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=28, bgcolor=SOFT_GREEN, border_radius=22)
        return ft.Column([
            hero,
            ft.Row([
                ft.Column([
                    ft.Text("A few pieces to get you started", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Choose a piece, then see how it feels in your room.",
                            size=12, color=ft.Colors.GREY_600)
                ], spacing=4),
                ft.Container(expand=True),
                ft.TextButton("Browse all decor", icon=ft.Icons.ARROW_FORWARD,
                              on_click=lambda _: self.navigate_to("catalog"))
            ]),
            self.product_grid
        ], expand=True, spacing=18)

    def refresh(self):
        self.product_grid.controls.clear()
        for product in database.get_products(category="Furniture")[:6]:
            icon_name = (product.get("icon") or "chair").replace("-", "_").upper()
            icon = getattr(ft.Icons, icon_name, ft.Icons.CHAIR)
            self.product_grid.controls.append(ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Icon(icon, color=DEEP_GREEN, size=24),
                                 padding=12, bgcolor=SOFT_GREEN, border_radius=12),
                    ft.Column([
                        ft.Text(product["name"], size=13, weight=ft.FontWeight.BOLD,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"${product['price']:,.2f}", size=12, color=ft.Colors.GREY_700)
                    ], spacing=5, expand=True)
                ], spacing=12),
                padding=14, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=15))
        try:
            self.update()
        except Exception:
            pass


def main(page: ft.Page):
    database.init_db()
    page.title = "Haven & Home | Home Decor"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = WARM_WHITE

    views = {}

    def navigate_to(key):
        if key not in views:
            return
        views[key].refresh()
        content_area.content = views[key]
        try:
            content_area.update()
        except Exception:
            pass
        page.update()

    views["home"] = HomeDecorHomeView(page, navigate_to)
    views["catalog"] = InventoryView(page)
    views["designer"] = RoomDesignerView(page)
    content_area = ft.AnimatedSwitcher(
        content=views["home"],
        transition=getattr(ft.AnimatedSwitcherTransition, "FADE", "fade")
        if hasattr(ft, "AnimatedSwitcherTransition") else "fade",
        duration=220, reverse_duration=160, expand=True)

    view_keys = ["home", "catalog", "designer"]

    def on_nav_change(index):
        rail.selected_index = index
        navigate_to(view_keys[index])

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=76,
        leading=ft.Container(height=8),
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.HOME_OUTLINED,
                                         selected_icon=ft.Icons.HOME, label="Home"),
            ft.NavigationRailDestination(icon=ft.Icons.CHAIR_OUTLINED,
                                         selected_icon=ft.Icons.CHAIR, label="Decor Catalog"),
            ft.NavigationRailDestination(icon=ft.Icons.AUTO_AWESOME_OUTLINED,
                                         selected_icon=ft.Icons.AUTO_AWESOME, label="Room Designer")
        ],
        on_change=lambda e: on_nav_change(e.control.selected_index))

    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.HOME, color=ft.Colors.WHITE, size=22),
                             padding=9, bgcolor=DEEP_GREEN, border_radius=12),
                ft.Column([
                    ft.Text("Haven & Home", size=17, weight=ft.FontWeight.BOLD, color=DEEP_GREEN),
                    ft.Text("HOME DECOR STUDIO", size=9, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_600)
                ], spacing=1)
            ], spacing=10),
            ft.FilledTonalButton("Design my room", icon=ft.Icons.AUTO_AWESOME,
                                 on_click=lambda _: navigate_to("designer"))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.symmetric(horizontal=22, vertical=12),
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        bgcolor=WARM_WHITE)

    page.add(ft.Column([
        header,
        ft.Row([rail, ft.VerticalDivider(width=1), content_area], expand=True, spacing=0)
    ], expand=True, spacing=0))


if __name__ == "__main__":
    view_mode = ft.AppView.FLET_APP
    if "--web" in sys.argv:
        view_mode = ft.AppView.WEB_BROWSER
    ft.run(main, view=view_mode)
