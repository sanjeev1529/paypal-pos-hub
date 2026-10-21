import io
import qrcode
from PIL import Image

def generate_qr_bytes(payload: str, box_size: int = 8, border: int = 2) -> bytes:
    """Generates PNG bytes of a QR code from any payload string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#003087", back_color="white")  # PayPal classic deep blue
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
