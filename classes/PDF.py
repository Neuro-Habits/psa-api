from PyPDF2 import PdfFileWriter, PdfFileReader
import sys
sys.path.append('../functions')
from functions.function import *
import os
import pathlib
from decouple import config

class PDF():
    def __init__(self,
                 attrs,
                 min_score = 0,
                 max_score = 10,
                 person = None
                 ):

        for k, v in attrs.items():
            setattr(self, k, v)

        lambda_env = config("LAMBDA_ENV")

        self.general_prefix = "/" if lambda_env == "True" else ""

        self.min_score = min_score
        self.max_score = max_score

        self.doc_center = 21.6

        self.out_pdf_file = self.general_prefix+"tmp/"+self.out_filename
        print(self.out_pdf_file)

        self.packet = io.BytesIO()
        self.output = PdfFileWriter()

    def generate_in_pdf_file_name(self):
        in_pdf_file = 'report_templates/'+self.report_folder+'/'+self.report_filename+'.pdf'

        return in_pdf_file

    def prep_pdf(self,
                 report_filename,
                 pages):

        self.report_filename = report_filename
        in_pdf_file = self.generate_in_pdf_file_name()

        template_pdf = PdfFileReader(open(in_pdf_file, "rb"))
        template_pdf_pagesize = template_pdf.getPage(0).mediaBox

        mod_pdf = PdfFileWriter()

        for i in pages:
            mod_pdf.addPage(template_pdf.getPage(i))

        tmp_pdf_filename = self.general_prefix+'tmp/tmp.pdf'

        with open(tmp_pdf_filename, 'wb+') as outfile:
            mod_pdf.write(outfile)

        final_template_pdf = PdfFileReader(open(tmp_pdf_filename, "rb"))

        c = canvas.Canvas(self.packet, pagesize=(template_pdf_pagesize.getWidth(), template_pdf_pagesize.getHeight()))

        return c, final_template_pdf

    def draw_score(self,
                   c,
                   score_offset,
                   offset_horizontal,
                   score_percentage,
                   offset_vertical,
                   height=32,
                   mask='auto',
                   preserveAspectRatio=True,
                   bias=True
                   ):

        if bias:
            bias = 3.23
        else:
            bias = 0
        offset_final = score_offset * (score_percentage/100)

        c.drawImage("resources/images/marker.png",
                    bias*cm + offset_horizontal*cm + offset_final*cm,
                    offset_vertical*cm,
                    height=height,
                    mask=mask,
                    preserveAspectRatio=preserveAspectRatio)

        return c

    def save_canvas(self,
                    out_pdf_file,
                    existing_pdf):
        # move to the beginning of the StringIO buffer
        self.packet.seek(0)

        new_pdf = PdfFileReader(self.packet)

        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.getPage(i)
            page.mergePage(new_pdf.getPage(i))
            self.output.addPage(page)

        if os.path.exists(out_pdf_file):
            try:
                os.remove(out_pdf_file)
                print("The file has been deleted successfully")
            except:
                print("An error occured")
        else:
            print("The file does not exist")

        outputStream = open(out_pdf_file, "wb")
        self.output.write(outputStream)
        outputStream.close()

        print("Saved report at "+out_pdf_file)