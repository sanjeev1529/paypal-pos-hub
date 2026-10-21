import uuid
import httpx
from datetime import datetime
import database

class PayPalService:
    def __init__(self):
        pass

    def get_config(self):
        settings = database.get_all_settings()
        mode = settings.get("paypal_mode", "sandbox")
        client_id = settings.get("paypal_client_id", "").strip()
        client_secret = settings.get("paypal_client_secret", "").strip()
        sim_mode = settings.get("simulation_mode", "true").lower() == "true"
        
        base_url = "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com"
        
        is_live_ready = bool(client_id and client_secret and not sim_mode)
        return {
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret,
            "base_url": base_url,
            "simulation_mode": not is_live_ready
        }

    def test_connection(self, client_id: str, client_secret: str, mode: str = "sandbox") -> dict:
        """Tests live PayPal OAuth authentication with the given credentials."""
        if not client_id or not client_secret:
            return {"success": False, "message": "Client ID and Client Secret must not be empty."}
        
        base_url = "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{base_url}/v1/oauth2/token",
                    data={"grant_type": "client_credentials"},
                    auth=(client_id, client_secret),
                    headers={"Accept": "application/json", "Accept-Language": "en_US"}
                )
                if response.status_code == 200:
                    data = response.json()
                    app_id = data.get("app_id", "PayPal App")
                    return {
                        "success": True,
                        "message": f"Successfully connected to PayPal {mode.upper()} API! (App ID: {app_id})"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"PayPal error ({response.status_code}): {response.text}"
                    }
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}

    def _get_access_token(self, cfg: dict) -> str:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                f"{cfg['base_url']}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(cfg["client_id"], cfg["client_secret"]),
                headers={"Accept": "application/json"}
            )
            res.raise_for_status()
            return res.json()["access_token"]

    def create_order(self, amount: float, currency: str = "USD", items: list = None, description: str = "POS Checkout Order") -> dict:
        """Creates a PayPal Checkout order (Live API or realistic Sandbox Simulation)."""
        cfg = self.get_config()

        # If simulation mode is active or no credentials provided
        if cfg["simulation_mode"]:
            order_id = f"PAYID-SIM{uuid.uuid4().hex[:12].upper()}"
            approval_link = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
            return {
                "order_id": order_id,
                "status": "CREATED",
                "mode": "Simulation (Sandbox)",
                "amount": amount,
                "currency": currency,
                "approval_url": approval_link,
                "qr_payload": approval_link,
                "simulated": True
            }

        # Real PayPal API call
        try:
            token = self._get_access_token(cfg)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "PayPal-Request-Id": str(uuid.uuid4())
            }
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": f"REF-{uuid.uuid4().hex[:8]}",
                        "description": description,
                        "amount": {
                            "currency_code": currency,
                            "value": f"{amount:.2f}"
                        }
                    }
                ],
                "application_context": {
                    "brand_name": database.get_setting("store_name", "Fintech Store"),
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": "https://example.com/checkout/success",
                    "cancel_url": "https://example.com/checkout/cancel"
                }
            }

            with httpx.Client(timeout=15.0) as client:
                res = client.post(f"{cfg['base_url']}/v2/checkout/orders", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

                approval_url = ""
                for link in data.get("links", []):
                    if link.get("rel") == "approve":
                        approval_url = link.get("href")
                        break

                return {
                    "order_id": data["id"],
                    "status": data.get("status", "CREATED"),
                    "mode": f"Live ({cfg['mode']})",
                    "amount": amount,
                    "currency": currency,
                    "approval_url": approval_url,
                    "qr_payload": approval_url or f"paypal:{data['id']}",
                    "simulated": False
                }
        except Exception as e:
            # Fallback to simulated order with error notice
            order_id = f"PAYID-FALLBACK{uuid.uuid4().hex[:10].upper()}"
            link = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
            return {
                "order_id": order_id,
                "status": "CREATED",
                "mode": "Sandbox Simulator (API fallback)",
                "amount": amount,
                "currency": currency,
                "approval_url": link,
                "qr_payload": link,
                "simulated": True,
                "api_notice": str(e)
            }

    def capture_order(self, order_id: str) -> dict:
        """Captures payment for an approved PayPal order."""
        cfg = self.get_config()

        if cfg["simulation_mode"] or order_id.startswith("PAYID-SIM") or order_id.startswith("PAYID-FALLBACK") or order_id.startswith("PAYID-MOCK"):
            return {
                "success": True,
                "order_id": order_id,
                "capture_id": f"CAP-{uuid.uuid4().hex[:10].upper()}",
                "status": "COMPLETED",
                "simulated": True,
                "message": "Payment captured successfully via Sandbox Simulator."
            }

        try:
            token = self._get_access_token(cfg)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "PayPal-Request-Id": str(uuid.uuid4())
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(f"{cfg['base_url']}/v2/checkout/orders/{order_id}/capture", headers=headers)
                res.raise_for_status()
                data = res.json()
                status = data.get("status", "COMPLETED")
                return {
                    "success": status == "COMPLETED",
                    "order_id": order_id,
                    "capture_id": data.get("id", order_id),
                    "status": status,
                    "simulated": False,
                    "message": "Payment captured successfully from PayPal!"
                }
        except Exception as e:
            return {
                "success": False,
                "order_id": order_id,
                "status": "FAILED",
                "simulated": False,
                "message": f"Capture error: {str(e)}"
            }

    def create_p2p_transfer(self, recipient_email: str, amount: float, currency: str = "USD", note: str = "") -> dict:
        """Executes a P2P send money transfer (deducts wallet, creates transaction)."""
        wallet = database.get_wallet()
        if wallet["balance"] < amount:
            return {"success": False, "message": f"Insufficient wallet balance (${wallet['balance']:.2f})."}

        # Deduct wallet
        new_balance = database.update_wallet_balance(-amount)

        # Record transaction
        tx_id = database.create_transaction(
            tx_type="transfer_sent",
            amount=amount,
            currency=currency,
            fee=0.0,
            net=-amount,
            status="completed",
            counterparty=recipient_email,
            paypal_order_id=f"P2P-{uuid.uuid4().hex[:8].upper()}",
            reference_note=note or f"Transfer to {recipient_email}"
        )

        return {
            "success": True,
            "tx_id": tx_id,
            "new_balance": new_balance,
            "message": f"Successfully sent ${amount:.2f} to {recipient_email}!"
        }

    def request_p2p_payment(self, amount: float, currency: str = "USD", note: str = "") -> dict:
        """Generates a payment request link and payload for QR code generation."""
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        store_name = database.get_setting("store_name", "Paypal App")
        # Standard PayPal.Me or checkout request URI
        uri = f"https://paypal.me/merchant?amount={amount:.2f}&currency={currency}&desc={note or 'Invoice'}"
        return {
            "request_id": req_id,
            "amount": amount,
            "currency": currency,
            "note": note,
            "qr_payload": uri
        }

paypal_service = PayPalService()
