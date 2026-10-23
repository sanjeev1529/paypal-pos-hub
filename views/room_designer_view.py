import asyncio
from pathlib import Path

import flet as ft

import database
from room_designer_service import design_room


NAVY = "#183B36"
MINT = "#DCEBE3"
SAND = "#F5F1E9"


class RoomDesignerView(ft.Container):
    """Catalog-led room visualization with a conversational design helper."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.app_page = page
        self.padding = ft.Padding.all(18)
        self.selected_product = None
        self.room_bytes = None
        self.room_filename = ""
        self.products = database.get_products(category="Furniture")
        self.picker = ft.FilePicker()
        self.preview = ft.Image(src=b"", width=390, height=280, fit=ft.BoxFit.COVER, border_radius=16, visible=False)
        self.empty_photo = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=38, color=NAVY),
                ft.Text("Your room photo will appear here", size=13, color=ft.Colors.GREY_700),
                ft.OutlinedButton("Upload an empty room", icon=ft.Icons.UPLOAD_FILE, on_click=self.pick_room),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            height=280, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW
        )
        self.photo_content = self.empty_photo
        self.result_area = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.AUTO_AWESOME, size=32, color=ft.Colors.GREY_400),
                ft.Text("Your furnished preview will appear here", color=ft.Colors.GREY_600, size=13),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            height=330, alignment=ft.Alignment.CENTER, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16, bgcolor=ft.Colors.SURFACE_CONTAINER_LOW
        )
        self.chat_line = ft.Text("Hi! Pick a piece from the furniture catalog, upload a photo of your empty room, and I’ll create a design preview.", size=13, color=ft.Colors.GREY_800)
        self.status_text = ft.Text("Choose a product and add a room photo to begin.", size=12, color=ft.Colors.GREY_600)
        self.style_notes = ft.TextField(
            label="Tell the designer what you like", hint_text="e.g. Place the sofa by the window; warm Scandinavian style",
            multiline=True, min_lines=2, max_lines=3, border_radius=12, text_size=13
        )
        self.generate_btn = ft.FilledButton(
            "Create room preview", icon=ft.Icons.AUTO_AWESOME, disabled=True,
            style=ft.ButtonStyle(bgcolor=NAVY, color=ft.Colors.WHITE), on_click=self.generate
        )
        self.content = self.build_ui()
        self.load_catalog()

    def build_ui(self):
        title = ft.Row([
            ft.Container(content=ft.Icon(ft.Icons.CHAIR_ALT, color=ft.Colors.WHITE, size=22), bgcolor=NAVY,
                         padding=10, border_radius=12),
            ft.Column([
                ft.Text("AI Room Designer", size=22, weight=ft.FontWeight.BOLD, color=NAVY),
                ft.Text("Choose a catalog piece and picture it in your space", size=12, color=ft.Colors.GREY_600)
            ], spacing=2),
            ft.Container(expand=True),
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=NAVY),
                                        ft.Text("DESIGN WITH AI", size=10, weight=ft.FontWeight.BOLD, color=NAVY)], spacing=6),
                         padding=ft.Padding.symmetric(horizontal=12, vertical=8), bgcolor=MINT, border_radius=20)
        ], spacing=12)
        catalog = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("1", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Choose furniture", size=16, weight=ft.FontWeight.BOLD)], spacing=8),
                ft.Text("Select one item from your store catalog.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=4),
                self.catalog_grid,
            ], spacing=10, expand=True), padding=16, border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )
        photo_card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("2", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Add your room photo", size=16, weight=ft.FontWeight.BOLD)], spacing=8),
                ft.Text("A clear, wide photo works best.", size=12, color=ft.Colors.GREY_600),
                self.photo_content,
                self.style_notes,
                ft.Row([self.generate_btn, self.status_text], spacing=12, wrap=True),
            ], spacing=12), padding=16, border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )
        assistant = ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=18),
                             bgcolor=NAVY, padding=8, border_radius=24),
                ft.Column([ft.Text("Room stylist", size=11, weight=ft.FontWeight.BOLD, color=NAVY), self.chat_line],
                          spacing=3, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=10),
            padding=14, bgcolor=SAND, border_radius=14
        )
        result_card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Your design preview", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True), ft.Icon(ft.Icons.HIGH_QUALITY_OUTLINED, color=NAVY)], spacing=6),
                self.result_area,
                ft.Text("AI previews are for inspiration. Product appearance may vary from the actual item.",
                        size=11, color=ft.Colors.GREY_600),
            ], spacing=12), padding=16, border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )
        self.catalog_panel = catalog
        self.photo_card = photo_card
        self.assistant_panel = assistant
        self.result_card = result_card
        return ft.Column([
            title,
            ft.Row([catalog, ft.Column([photo_card, assistant], spacing=12)], expand=True, spacing=14,
                   vertical_alignment=ft.CrossAxisAlignment.START),
            result_card
        ], spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)

    @property
    def catalog_grid(self):
        if not hasattr(self, "_catalog_grid"):
            self._catalog_grid = ft.GridView(expand=True, runs_count=2, max_extent=210,
                                             child_aspect_ratio=1.28, spacing=8, run_spacing=8)
        return self._catalog_grid

    @property
    def photo_content(self):
        return self._photo_content

    @photo_content.setter
    def photo_content(self, value):
        self._photo_content = value

    def load_catalog(self):
        self.catalog_grid.controls.clear()
        for product in self.products:
            selected = self.selected_product and product["id"] == self.selected_product["id"]
            card = ft.Container(
                content=ft.Column([
                    ft.Icon(getattr(ft.Icons, product.get("icon", "chair").upper(), ft.Icons.CHAIR), size=25, color=NAVY),
                    ft.Text(product["name"], size=12, weight=ft.FontWeight.BOLD, max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"${product['price']:,.2f}", size=11, color=ft.Colors.GREY_700),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                padding=12, border_radius=12, bgcolor=MINT if selected else ft.Colors.SURFACE,
                border=ft.Border.all(2 if selected else 1, NAVY if selected else ft.Colors.OUTLINE_VARIANT),
                on_click=lambda _, p=product: self.select_product(p), ink=True,
                animate_scale=ft.Animation(150, "easeOut") if hasattr(ft, "Animation") else 150,
                animate=ft.Animation(150, "easeOut") if hasattr(ft, "Animation") else 150,
            )

            def make_card_hover(c_ref, is_sel):
                def on_hover(e):
                    is_h = str(getattr(e, "data", "")).lower() == "true"
                    c_ref.scale = 1.04 if is_h else 1.0
                    c_ref.shadow = ft.BoxShadow(blur_radius=12, color=ft.Colors.BLACK_12, offset=ft.Offset(0, 3)) if is_h else None
                    try:
                        c_ref.update()
                    except Exception:
                        pass
                return on_hover

            card.on_hover = make_card_hover(card, selected)
            self.catalog_grid.controls.append(card)

    def select_product(self, product):
        self.selected_product = product
        self.chat_line.value = f"Nice choice — {product['name']} is selected. Upload the room photo and tell me any placement or color preferences."
        self.refresh_ready_state()
        self.load_catalog()
        self.safe_update()

    async def pick_room(self, _):
        files = await self.picker.pick_files(dialog_title="Choose an empty room photo", file_type=ft.FilePickerFileType.IMAGE,
                                             allowed_extensions=["png", "jpg", "jpeg"], with_data=True)
        if not files:
            return
        room_file = files[0]
        self.room_filename = room_file.name
        self.room_bytes = room_file.bytes
        if not self.room_bytes and room_file.path:
            self.room_bytes = await asyncio.to_thread(Path(room_file.path).read_bytes)
        if not self.room_bytes:
            self.status_text.value = "Could not read that photo. Please choose another image."
            self.safe_update()
            return
        self.preview.src = self.room_bytes
        self.preview.visible = True
        self.photo_content = ft.Column([
            self.preview,
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=16),
                    ft.Text(self.room_filename, size=11, color=ft.Colors.GREY_700, expand=True),
                    ft.TextButton("Replace", on_click=self.pick_room)], spacing=6)
        ], spacing=6)
        self.photo_card.content.controls[2] = self.photo_content
        self.chat_line.value = "Got the room photo. I’ll preserve the room layout and place your selected piece into it."
        self.refresh_ready_state()
        self.safe_update()

    def refresh_ready_state(self):
        self.generate_btn.disabled = not (self.selected_product and self.room_bytes)
        if self.generate_btn.disabled:
            self.status_text.value = "Choose a product and add a room photo to begin."
        else:
            self.status_text.value = f"Ready to style with {self.selected_product['name']}"

    async def generate(self, _):
        if not self.selected_product or not self.room_bytes:
            return
        self.generate_btn.disabled = True
        self.generate_btn.text = "Creating your room..."
        self.generate_btn.icon = ft.Icons.HOURGLASS_TOP
        self.status_text.value = "The designer is furnishing your room. This can take a minute."
        self.chat_line.value = f"I’m placing the {self.selected_product['name']} in your room now."
        self.safe_update()
        try:
            image_bytes = await asyncio.to_thread(
                design_room, self.room_bytes, self.room_filename, self.selected_product, self.style_notes.value or ""
            )
        except Exception as exc:
            self.status_text.value = str(exc)
            self.chat_line.value = "I couldn’t finish that preview. Check the setup and try again."
        else:
            self.result_area.content = ft.Image(src=image_bytes, width=600, height=390, fit=ft.BoxFit.CONTAIN, border_radius=12)
            self.result_area.bgcolor = ft.Colors.BLACK
            self.status_text.value = "Your design preview is ready."
            self.chat_line.value = f"Here’s your room with the {self.selected_product['name']}. Want to try another item or adjust your style notes?"
        finally:
            self.generate_btn.disabled = False
            self.generate_btn.text = "Create room preview"
            self.generate_btn.icon = ft.Icons.AUTO_AWESOME
            self.safe_update()

    def safe_update(self):
        try:
            self.update()
        except Exception:
            pass

    def refresh(self):
        self.products = database.get_products(category="Furniture")
        self.load_catalog()
        self.safe_update()
