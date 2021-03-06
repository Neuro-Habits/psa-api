from PyPDF2 import PdfFileWriter, PdfFileReader
import sys
sys.path.append('../functions')
from functions.function import *
import pathlib

class PDF():
    def __init__(self,
                 attrs,
                 min_score = 1,
                 max_score = 10,
                 person = None
                 ):

        for k, v in attrs.items():
            setattr(self, k, v)

        self.min_score = min_score
        self.max_score = max_score

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
                   preserveAspectRatio=True
                   ):

        offset_final = score_offset * (score_percentage/100)

        c.drawImage("resources/images/marker.png",
                    offset_horizontal+offset_final,
                    offset_vertical,
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

        outputStream = open(out_pdf_file, "wb")
        self.output.write(outputStream)
        outputStream.close()

        print("Saved report at "+out_pdf_file)

    def create_scores_list(self,
                           person,
                           variables):

        scores_list = []
        for variable in variables:
            scores_list.append(getattr(person, variable))

        return scores_list


    def calculate_final_scores(self,
                               person,
                               variables):

        scores_list = self.create_scores_list(person, variables)
        print(variables)

        perc = []

        for score in scores_list:
            perc.append(
                percentage_from_score(self.min_score, self.max_score, score)
            )

        print("perc:")
        print(perc)

        return perc