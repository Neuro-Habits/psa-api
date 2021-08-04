import boto3
from botocore.exceptions import ClientError
import io

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics  
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import utils
from reportlab.platypus import Frame, Image
from pathlib import Path

# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
# from google.oauth2 import service_account

from email import encoders
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# def authenticate(SCOPES):
#     SECRET_FILENAME = 'client_secret.json'
#     SERVICE_ACCOUNT_FILE = str(Path(Path().resolve(), SECRET_FILENAME))

#     creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            
#     return creds

def uploadFile(service, filename):
    file_metadata = {
        'name': filename,
        'mimeType': 'application/pdf',
        #'parents': [myDriveId]
    }
    media = MediaFileUpload(file_metadata['name'],
                            mimetype='application/pdf',
                            resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print ('File ID: ' + file.get('id'))
    
    return file.get('id')

def generate_pdf_from_template(person, out_pdf_file):
    def score(c):
        c.setFont('Montserrat-Italic', 30)
        c.setFillColorRGB(1, 1, 1)
        c.rect(center_coords-4,630,cm,cm,fill=1, stroke=0)
        c.setFillColorRGB(74/256, 97/256, 121/256)
        c.drawCentredString(center_coords, PAGE_HEIGHT-212, str(person.score))
        
    font_folder = str(Path("fonts"))
    
    pdfmetrics.registerFont(TTFont('Montserrat-Regular', Path(font_folder,'Montserrat-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Montserrat-Italic', Path(font_folder,'Montserrat-Italic.ttf')))

    PAGE_WIDTH  = defaultPageSize[0]
    PAGE_HEIGHT = defaultPageSize[1]
    
    center_coords = PAGE_WIDTH/2.0

    from PyPDF2 import PdfFileWriter, PdfFileReader
    import io
 
    in_pdf_file = 'report_templates/stress_quickscan/stress.pdf'
 
    packet = io.BytesIO()
    c = canvas.Canvas(packet)

    c.showPage()
    c.showPage()
    score(c)
    c.showPage()
    c.showPage()
    c.showPage()
    c.showPage()
    c.showPage()
    c.showPage()
    c.save()
 
    #move to the beginning of the StringIO buffer
    packet.seek(0)
 
    new_pdf = PdfFileReader(packet)
 
    # read the existing PDF
    existing_pdf = PdfFileReader(open(in_pdf_file, "rb"))
    output = PdfFileWriter()
 
    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.getPage(i)
        page.mergePage(new_pdf.getPage(i))
        output.addPage(page)
 
    outputStream = open(out_pdf_file, "wb")
    output.write(outputStream)
    outputStream.close()

def send_mail_with_attachment(person, sender, aws_region, subject, report_id):
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "Beste,\r\nZie bijgevoegd het resultaat van uw PSA verzoek."

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <p>Beste,</p>
    <p>Zie bijgevoegd het resultaat van uw PSA verzoek.</p>
    </body>
    </html>
    """

    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=aws_region)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = subject 
    msg['From'] = sender 
    msg['To'] = person.email

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(report_id, 'rb').read())

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header('Content-Disposition','attachment',filename="stressrapport_quickscan.pdf")

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)
    try:
        #Provide the contents of the email.
        response = client.send_raw_email(
            Source=sender,
            Destinations=[
                person.email
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent to "+person.email+"! Message ID:"),
        print(response['MessageId'])
        
def fill_page_with_image(path, canvas):
    """
    Given the path to an image and a reportlab canvas, fill the current page
    with the image.
    
    This function takes into consideration EXIF orientation information (making
    it compatible with photos taken from iOS devices).
    
    This function makes use of ``canvas.setPageRotation()`` and
    ``canvas.setPageSize()`` which will affect subsequent pages, so be sure to
    reset them to appropriate values after calling this function.
    
    :param   path: filesystem path to an image
    :param canvas: ``reportlab.canvas.Canvas`` object
    """
    from PIL import Image

    page_width, page_height = canvas._pagesize

    image = Image.open(path)
    image_width, image_height = image.size
    if hasattr(image, '_getexif'):
        orientation = image._getexif().get(274, 1)  # 274 = Orientation
    else:
        orientation = 1

    # These are the possible values for the Orientation EXIF attribute:
    ORIENTATIONS = {
        1: "Horizontal (normal)",
        2: "Mirrored horizontal",
        3: "Rotated 180",
        4: "Mirrored vertical",
        5: "Mirrored horizontal then rotated 90 CCW",
        6: "Rotated 90 CW",
        7: "Mirrored horizontal then rotated 90 CW",
        8: "Rotated 90 CCW",
    }
    draw_width, draw_height = page_width, page_height
    if orientation == 1:
        canvas.setPageRotation(0)
    elif orientation == 3:
        canvas.setPageRotation(180)
    elif orientation == 6:
        image_width, image_height = image_height, image_width
        draw_width, draw_height = page_height, page_width
        canvas.setPageRotation(90)
    elif orientation == 8:
        image_width, image_height = image_height, image_width
        draw_width, draw_height = page_height, page_width
        canvas.setPageRotation(270)
    else:
        raise ValueError("Unsupported image orientation '%s'."
                         % ORIENTATIONS[orientation])

    if image_width > image_height:
        page_width, page_height = page_height, page_width  # flip width/height
        draw_width, draw_height = draw_height, draw_width
        canvas.setPageSize((page_width, page_height))

    canvas.drawImage(path, 0, 0, width=draw_width, height=draw_height,
                     preserveAspectRatio=True)