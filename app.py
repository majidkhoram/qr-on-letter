import os
from flask import Flask, request, send_file, abort
from werkzeug.utils import secure_filename
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from qrcode import QRCode
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = '/path/to/upload/folder'
ALLOWED_EXTENSIONS = {'pdf'}
BASE_URL = 'https://dl.cinvu.net/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_qr_code(data):
    qr = QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    qr_drawing = Drawing(1 * inch, 1 * inch)
    qr_drawing.add(qr.make_image(fill_color="black", back_color="white"))
    return qr_drawing

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, description="No file part")
    file = request.files['file']
    if file.filename == '':
        abort(400, description="No selected file")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Generate MD5 sum
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        md5sum = file_hash.hexdigest()
        
        # Generate QR code
        url = f"{BASE_URL}{md5sum}"
        qr_code = generate_qr_code(url)
        
        # Add QR code to PDF
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        renderPDF.draw(qr_code, can, 450, 750)  # Adjust position as needed
        can.save()
        packet.seek(0)
        
        new_pdf = PdfReader(packet)
        existing_pdf = PdfReader(file_path)
        output = PdfWriter()
        
        page = existing_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
        
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{md5sum}.pdf")
        with open(output_path, "wb") as outputStream:
            output.write(outputStream)
        
        return md5sum, 201

@app.route('/<md5sum>', methods=['GET'])
def download_file(md5sum):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{md5sum}.pdf")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        abort(404, description="File not found")

if __name__ == '__main__':
    app.run()
