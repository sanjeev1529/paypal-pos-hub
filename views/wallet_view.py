import flet as ft
import database
from paypal_service import paypal_service
from qr_service import generate_qr_bytes

class WalletView(ft.Container):
    def __init__(self, page: ft.Page, on_transaction_completed=None, initial_tab=0):
        super().__init__(expand=True)
        self.page = page
        self.on_transaction_completed = on_transaction_completed
        self.active_tab = initial_tab
        self.padding = ft.padding.all(20)

        # Send Tab Inputs
        self.send_recipient = ft.TextField(
            label="Recipient Email or PayPal ID",
            hint_text="e.g. partner@example.com",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=ft.border_radius.all(10)
        )
        self.send_amount = ft.TextField(
            label="Amount ($)",
            hint_text="0.00",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            border_radius=ft.border_radius.all(10),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.send_note = ft.TextField(
            label="What is this for? (Optional)",
            hint_text="e.g. Invoice payment or dinner split",
            prefix_icon=ft.Icons.NOTES,
            border_radius=ft.border_radius.all(10)
        )

        # Request Tab Inputs
        self.req_amount = ft.TextField(
            label="Requested Amount ($)",
            hint_text="50.00",
            value="50.00",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            border_radius=ft.border_radius.all(10),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.req_note = ft.TextField(
            label="Request Description",
            hint_text="e.g. Consultation fee",
            value="Payment Request",
            prefix_icon=ft.Icons.DESCRIPTION,
            border_radius=ft.border_radius.all(10)
        )
        self.qr_container = ft.Container(alignment=ft.alignment.center)

        # Deposit / Withdraw Inputs
        self.deposit_amount = ft.TextField(
            label="Deposit Amount ($)",
            hint_text="100.00",
            prefix_icon=ft.Icons.ADD_CARD,
            border_radius=ft.border_radius.all(10),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        self.withdraw_amount = ft.TextField(
            label="Withdrawal Amount ($)",
            hint_text="100.00",
            prefix_icon=ft.Icons.ACCOUNT_BALANCE,
            border_radius=ft.border_radius.all(10),
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.content = self.build_ui()

    def build_ui(self):
        wallet = database.get_wallet()
        balance = wallet["balance"]

        # Header balance card
        balance_card = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("CURRENT AVAILABLE BALANCE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
                    ft.Text(f"${balance:,.2f}", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(f"Currency: {wallet['currency']} • Status: Active", size=12, color=ft.Colors.WHITE70),
                ], spacing=4),
                ft.Container(
                    content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.WHITE, size=36),
                    bgcolor=ft.Colors.WHITE24,
                    padding=ft.padding.all(14),
                    border_radius=ft.border_radius.all(14)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(22),
            border_radius=ft.border_radius.all(16),
            gradient=ft.LinearGradient(
                colors=["#003087", "#0079C1"]
            )
        )

        # Preset amount helper buttons
        def set_preset_amount(amt: float):
            self.send_amount.value = f"{amt:.2f}"
            self.send_amount.update()

        preset_row = ft.Row([
            ft.Text("Quick amounts:", size=12, color=ft.Colors.GREY_600),
            ft.OutlinedButton("$10", on_click=lambda _: set_preset_amount(10)),
            ft.OutlinedButton("$25", on_click=lambda _: set_preset_amount(25)),
            ft.OutlinedButton("$50", on_click=lambda _: set_preset_amount(50)),
            ft.OutlinedButton("$100", on_click=lambda _: set_preset_amount(100)),
        ], spacing=6)

        # Tab 1: Send Card
        send_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SEND, color="#003087"),
                    ft.Text("Send Money via PayPal / Wallet", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                ft.Text("Send funds instantly to any email address or PayPal account.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=10),
                self.send_recipient,
                self.send_amount,
                preset_row,
                self.send_note,
                ft.Container(height=6),
                ft.FilledButton(
                    "Send Money Now",
                    icon=ft.Icons.SEND,
                    style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE),
                    on_click=self.handle_send_money
                )
            ], spacing=12),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True
        )

        # Tab 2: Request / QR Card
        request_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.QR_CODE_SCANNER, color="#003087"),
                    ft.Text("Receive / Request Money", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                ft.Text("Generate a dynamic PayPal payment QR code to collect money.", size=12, color=ft.Colors.GREY_600),
                ft.Divider(height=10),
                self.req_amount,
                self.req_note,
                ft.FilledButton(
                    "Generate Payment QR Code",
                    icon=ft.Icons.QR_CODE,
                    style=ft.ButtonStyle(bgcolor="#0079C1", color=ft.Colors.WHITE),
                    on_click=self.handle_generate_qr
                ),
                self.qr_container
            ], spacing=12),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True
        )

        # Bottom Deposit & Withdraw Row
        deposit_card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.ADD_CARD, color=ft.Colors.GREEN_700), ft.Text("Add Funds (Top-Up)", weight=ft.FontWeight.BOLD, size=15)], spacing=8),
                self.deposit_amount,
                ft.FilledButton("Top-Up Wallet", icon=ft.Icons.ADD, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE), on_click=self.handle_deposit)
            ], spacing=10),
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True
        )

        withdraw_card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.ACCOUNT_BALANCE, color=ft.Colors.BLUE_700), ft.Text("Withdraw to Bank", weight=ft.FontWeight.BOLD, size=15)], spacing=8),
                self.withdraw_amount,
                ft.FilledButton("Withdraw Funds", icon=ft.Icons.CALL_MADE, style=ft.ButtonStyle(bgcolor="#003087", color=ft.Colors.WHITE), on_click=self.handle_withdraw)
            ], spacing=10),
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True
        )

        return ft.ListView([
            balance_card,
            ft.Container(height=16),
            ft.Row([send_card, request_card], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Container(height=16),
            ft.Row([deposit_card, withdraw_card], spacing=16)
        ], spacing=0, expand=True)

    def handle_send_money(self, _):
        recipient = self.send_recipient.value.strip()
        amount_str = self.send_amount.value.strip()
        note = self.send_note.value.strip()

        if not recipient:
            self.show_snack("Please enter a recipient email or PayPal ID.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.show_snack("Please enter a valid transfer amount greater than $0.")
            return

        wallet = database.get_wallet()
        if wallet["balance"] < amount:
            self.show_snack(f"Insufficient funds! Your balance is ${wallet['balance']:.2f}")
            return

        # Execute P2P Transfer
        res = paypal_service.create_p2p_transfer(recipient, amount, "USD", note)
        if res["success"]:
            self.send_recipient.value = ""
            self.send_amount.value = ""
            self.send_note.value = ""
            self.content = self.build_ui()
            self.update()
            if self.on_transaction_completed:
                self.on_transaction_completed()
            self.show_snack(f"✓ ${amount:.2f} sent to {recipient} successfully!")
        else:
            self.show_snack(f"Error: {res.get('message')}")

    def handle_generate_qr(self, _):
        try:
            amount = float(self.req_amount.value.strip())
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.show_snack("Please enter a valid requested amount.")
            return

        note = self.req_note.value.strip()
        req_data = paypal_service.request_p2p_payment(amount, "USD", note)
        qr_bytes = generate_qr_bytes(req_data["qr_payload"], box_size=5)

        def simulate_incoming_payment(_):
            # Simulate customer scanning and paying
            database.update_wallet_balance(amount)
            database.create_transaction(
                tx_type="transfer_received",
                amount=amount,
                currency="USD",
                fee=0.0,
                net=amount,
                status="completed",
                counterparty="Customer QR Payment",
                paypal_order_id=req_data["request_id"],
                reference_note=f"Payment for {note or 'Invoice'}"
            )
            self.content = self.build_ui()
            self.update()
            if self.on_transaction_completed:
                self.on_transaction_completed()
            self.show_snack(f"✓ Received ${amount:.2f} payment from customer!")

        self.qr_container.content = ft.Container(
            content=ft.Column([
                ft.Divider(height=10),
                ft.Text(f"Scan to Pay ${amount:.2f} via PayPal:", size=13, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(src=qr_bytes, width=160, height=160),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(8),
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=ft.border_radius.all(8)
                ),
                ft.Text(f"Invoice Reference: {req_data['request_id']}", size=11, color=ft.Colors.GREY_600),
                ft.FilledTonalButton(
                    "Simulate Customer Payment Arrival",
                    icon=ft.Icons.CHECK_CIRCLE,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100, color=ft.Colors.GREEN_900),
                    on_click=simulate_incoming_payment
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=ft.padding.all(10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=ft.border_radius.all(10)
        )
        self.update()

    def handle_deposit(self, _):
        try:
            amt = float(self.deposit_amount.value.strip())
            if amt <= 0:
                raise ValueError()
        except ValueError:
            self.show_snack("Please enter a valid deposit amount.")
            return

        database.update_wallet_balance(amt)
        database.create_transaction(
            tx_type="wallet_deposit",
            amount=amt,
            currency="USD",
            fee=0.0,
            net=amt,
            status="completed",
            counterparty="Bank Account (Deposit)",
            paypal_order_id="DEP-WALLET",
            reference_note=f"Manual wallet top-up"
        )
        self.deposit_amount.value = ""
        self.content = self.build_ui()
        self.update()
        if self.on_transaction_completed:
            self.on_transaction_completed()
        self.show_snack(f"✓ Added ${amt:.2f} to wallet balance!")

    def handle_withdraw(self, _):
        try:
            amt = float(self.withdraw_amount.value.strip())
            if amt <= 0:
                raise ValueError()
        except ValueError:
            self.show_snack("Please enter a valid withdrawal amount.")
            return

        wallet = database.get_wallet()
        if wallet["balance"] < amt:
            self.show_snack("Insufficient funds to withdraw.")
            return

        database.update_wallet_balance(-amt)
        database.create_transaction(
            tx_type="wallet_withdraw",
            amount=amt,
            currency="USD",
            fee=0.0,
            net=-amt,
            status="completed",
            counterparty="Bank Account (Withdrawal)",
            paypal_order_id="WTH-BANK",
            reference_note=f"Withdrawal to linked account"
        )
        self.withdraw_amount.value = ""
        self.content = self.build_ui()
        self.update()
        if self.on_transaction_completed:
            self.on_transaction_completed()
        self.show_snack(f"✓ Initiated withdrawal of ${amt:.2f} to bank account!")

    def show_snack(self, msg: str):
        self.page.show_dialog(ft.SnackBar(ft.Text(msg)))

    def refresh(self):
        self.content = self.build_ui()
        self.update()
