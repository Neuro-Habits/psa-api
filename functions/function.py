import boto3
from botocore.exceptions import ClientError
import io
import os
import requests

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

from collections import defaultdict

# def authenticate(SCOPES):
#     SECRET_FILENAME = 'client_secret.json'
#     SERVICE_ACCOUNT_FILE = str(Path(Path().resolve(), SECRET_FILENAME))

#     creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            
#     return creds

def percentage_from_score(min_score, max_score, score):
    perc = (score - min_score) / (max_score - min_score) * 100
    return perc

def create_dict_with_lists(lst):
    # using loop to get dictionaries
    # defaultdict used to make default empty list
    # for each key
    res = defaultdict(list)
    for sub in lst:
        for key in sub:
            res[key].append(sub[key])

    return res

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

# def generate_pdf_from_template(person, out_pdf_file, api_prefix, in_filename, MIN_SCORE, MAX_SCORE):
#     from PyPDF2 import PdfFileWriter, PdfFileReader
#     import io
#
#     SCORE_OFFSET = 261
#
#     perc = percentage_from_score(MIN_SCORE, MAX_SCORE, person.score)
#
#     OFFSET_FINAL = SCORE_OFFSET * (perc/100)
#
#     if perc <= percentage_from_score(MIN_SCORE, MAX_SCORE, 3):
#         feedback_color = "green"
#     elif perc <= percentage_from_score(MIN_SCORE, MAX_SCORE, 7):
#         feedback_color = "yellow"
#     else:
#         feedback_color = "red"
#
#     print(feedback_color)
#
#     # read the existing PDF
#     in_pdf_file = api_prefix+'report_templates/stress_quickscan/'+in_filename+'_'+feedback_color+'.pdf'
#
#     existing_pdf = PdfFileReader(open(in_pdf_file, "rb"))
#     existing_pdf_pagesize = existing_pdf.getPage(0).mediaBox
#     output = PdfFileWriter()
#
#     def score(c):
#         c.drawImage(api_prefix+"resources/images/marker.png",
#                     127+OFFSET_FINAL,
#                     307,
#                     height=32,
#                     mask='auto',
#                     preserveAspectRatio=True)
#
#     font_folder = str(Path(api_prefix, "fonts"))
#
#     pdfmetrics.registerFont(TTFont('Montserrat-Regular', Path(font_folder,'Montserrat-Regular.ttf')))
#     pdfmetrics.registerFont(TTFont('Montserrat-Italic', Path(font_folder,'Montserrat-Italic.ttf')))
#
#     PAGE_WIDTH  = defaultPageSize[0]
#     PAGE_HEIGHT = defaultPageSize[1]
#
#     center_coords = PAGE_WIDTH/2.0
#
#     packet = io.BytesIO()
#     c = canvas.Canvas(packet, pagesize=(existing_pdf_pagesize.getWidth(),existing_pdf_pagesize.getHeight()))
#
#     c.showPage()
#     score(c)
#     c.showPage()
#     c.showPage()
#     c.showPage()
#     c.showPage()
#     c.showPage()
#     c.showPage()
#     c.showPage()
#     c.save()
#
#     #move to the beginning of the StringIO buffer
#     packet.seek(0)
#
#     new_pdf = PdfFileReader(packet)
#
#     for i in range(len(existing_pdf.pages)):
#         page = existing_pdf.getPage(i)
#         page.mergePage(new_pdf.getPage(i))
#         output.addPage(page)
#
#     outputStream = open(out_pdf_file, "wb")
#     output.write(outputStream)
#     outputStream.close()

def fetch_form_id(name, stage, init_info):
    for init in init_info:
        if init['type'] == name:
            for t in init['stage']:
                if t['stage'] == stage:
                    form_id = t['form_id']

    return form_id

def send_mail_with_attach_ses(sender, recipient, aws_region, subject, filepath, person, link):
    # link = "https://preview.mailerlite.com/i6e0h6"
    f = requests.get(link)

    html_text = f.text
    html_text = html_text.replace("Afmelden", "")
    
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ""

    # The HTML body of the email.
    BODY_HTML = html_text

    CHARSET = "utf-8"
    client = boto3.client('ses',region_name=aws_region)

    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = subject 
    msg['From'] = sender 
    msg['To'] = recipient

    msg_body = MIMEMultipart('alternative')
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(filepath, 'rb').read())

    att.add_header('Content-Disposition','attachment',filename=os.path.basename(filepath))

    if os.path.exists(filepath):
        print("File exists")
    else:
        print("File does not exists")

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)

    try:
        #Provide the contents of the email.
        response = client.send_raw_email(
            Source=msg['From'],
            Destinations=[
                msg['To']
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
            ConfigurationSetName="ConfigSet"
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])