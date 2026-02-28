# pip install qrcode[pil]

import qrcode
from qrcode.constants import ERROR_CORRECT_M

link = "https://zhan.care/questionnaire/"
out_file = "zhan_care_questionnaire_qr.png"

qr = qrcode.QRCode(
    version=None,                 # auto fit
    error_correction=ERROR_CORRECT_M,
    box_size=12,                  # pixel size of each box
    border=4
)

qr.add_data(link)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save(out_file)

print(f"Saved QR to: {out_file}")
