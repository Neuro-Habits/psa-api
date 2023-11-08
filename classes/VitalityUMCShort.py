from classes.PDF import *
import sys
sys.path.append('../functions')
from functions.function import *
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color, black, blue, red
from reportlab.lib.pagesizes import A4
import numpy as np

custom_style = ParagraphStyle('custom_style',
                              fontName="Montserrat-Medium",
                              fontSize = 10,
                              textColor = Color(0,0,0,1)
                              )


class VitalityUMCShort(PDF):
    def __init__(self,
                 attrs,
                 person = None):

        self.attrs = attrs

        for k, v in self.attrs.items():
            setattr(self, k, v)

    def init_super(self):
        PDF.__init__(self,
                     self.attrs,
                     person = self.person
                     )

    def cutoff(self, subject):
        value = getattr(self.person, subject)
        subject = self.page_attrs[subject]
        
        length = len(subject['text'])
        for i in range(length):
            if i < length-1:
                if subject['cutoff_score'][i] <= value < subject['cutoff_score'][i + 1]:
                    cutoff_color = subject['colors'][i]
                    cutoff_text = subject['text'][i]

            elif i == length-1:
                if value >= subject['cutoff_score'][i]:
                    cutoff_color = subject['colors'][i]
                    cutoff_text = subject['text'][i]

        return cutoff_color, cutoff_text


    def create_canvas(self):
        font_folder = str(Path("", "fonts"))

        x_leftAlign = -(self.doc_center / 2)
        arrow_x = x_leftAlign*cm + 0.29*cm
        textBoxWidth = 8.5*cm

        pdfmetrics.registerFont(TTFont('Montserrat-SemiBold', Path(font_folder,'Montserrat-SemiBold.ttf')))
        pdfmetrics.registerFont(TTFont('Montserrat-Regular', Path(font_folder,'Montserrat-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Montserrat-Medium', Path(font_folder,'Montserrat-Medium.ttf')))

        pages = range(6)

        height = 19

        c, existing_pdf = self.prep_pdf(self.report_filename_in, pages)
        c.showPage()
        c.showPage()

        ## Werkdruk
        subject = "Werkdruk"
        sub_attrs = self.page_attrs[subject]
        print(percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)))

        self.draw_score(c,
                        sub_attrs['score_offset'],
                        x_leftAlign + sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    arrow_x,
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,textBoxWidth,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Overuren
        subject = "Overuren"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    arrow_x,
                    11*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]

        self.draw_score(c,
                        sub_attrs['score_offset'],
                        x_leftAlign + sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        frame = Frame(1.5*cm, 8.3*cm,textBoxWidth,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Autonomie
        subject = "Autonomie"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        x_leftAlign + sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    arrow_x,
                    4.8*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 2.2*cm,textBoxWidth,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Sociale steun collega's, functionele steun collega's, autonomie

        ## Burn-out klachten
        subject = "Burn-out klachten"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        x_leftAlign + sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    arrow_x,
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,textBoxWidth,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Bevlogenheid
        subject = "Bevlogenheid"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    arrow_x,
                    11.4*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        x_leftAlign + sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        frame = Frame(1.5*cm, 8.7*cm,textBoxWidth,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Burn-out klachten, bevlogenheid
        c.showPage()
        c.showPage()

        c.save()

        self.save_canvas(self.out_pdf_file,
                         existing_pdf)