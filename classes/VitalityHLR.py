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


class VitalityHLR(PDF):
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

        print(subject)
        print(value)
        print("---")

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
        pdfmetrics.registerFont(TTFont('Montserrat-SemiBold', Path(font_folder,'Montserrat-SemiBold.ttf')))
        pdfmetrics.registerFont(TTFont('Montserrat-Regular', Path(font_folder,'Montserrat-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Montserrat-Medium', Path(font_folder,'Montserrat-Medium.ttf')))

        report_filename = "PSA rapport vitaliteit V.2"
        pages = range(10)

        height = 19

        c, existing_pdf = self.prep_pdf(report_filename, pages)
        c.showPage()
        c.showPage()

        ## Werkdruk
        subject = "Werkdruk"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Overuren
        subject = "Overuren"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    11*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        frame = Frame(1.5*cm, 8.3*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Emotionele belasting
        subject = "Emotionele belasting"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical'],
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    4.1*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 1.5*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Werkdruk, overuren, emotionele belasting

        ## Cognitieve belasting
        subject = "Cognitieve belasting"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Sociale steun leidinggevende
        subject = "Sociale steun leidinggevende"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    11.2*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        frame = Frame(1.5*cm, 8.5*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Functionele steun leidinggevende
        subject = "Functionele steun leidinggevende"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    3.9*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 1.3*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Cognitieve belasting, sociale steun leidinggevende, functionele steun leidinggevende

        ## Sociale steun collegae
        subject = "Sociale steun collegae"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Functionele steun collegae,
        subject = "Functionele steun collegae"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    11.4*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        frame = Frame(1.5*cm, 8.7*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Autonomie
        subject = "Autonomie"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    4.8*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 2.2*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Sociale steun collega's, functionele steun collega's, autonomie

        ## Ongewenst gedrag intern
        subject = "Ongewenst gedrag intern"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Ongewenst gedrag extern
        subject = "Ongewenst gedrag extern"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    11.4*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        frame = Frame(1.5*cm, 8.7*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Ongewenst gedrag intern, ongewenst gedrag extern, ontwikkelmogelijkheden

        ## Burn-out klachten
        subject = "Burn-out klachten"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Bevlogenheid
        subject = "Bevlogenheid"
        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    11.4*cm,
                    height=25,
                    preserveAspectRatio=True)

        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        frame = Frame(1.5*cm, 8.7*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        ## Tevredenheid
        subject = "Tevredenheid"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject)),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    4.8*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 2.2*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Burn-out klachten, bevlogenheid, tevredenheid

        ## Organisatiecultuur
        subject = "Organisatiecultuur"
        sub_attrs = self.page_attrs[subject]
        self.draw_score(c,
                        sub_attrs['score_offset'],
                        sub_attrs['offset_horizontal'],
                        percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'],getattr(self.person, subject), rotate=True),
                        sub_attrs['offset_vertical']*cm,
                        height = height)

        c.drawImage("resources/images/arrow_"+self.cutoff(subject)[0]+".png",
                    (-10.93*cm)+(0.4*cm),
                    18.7*cm,
                    height=25,
                    preserveAspectRatio=True)

        frame = Frame(1.5*cm, 16.1*cm,8*cm,100, showBoundary=0)
        story = [Paragraph(self.cutoff(subject)[1], custom_style)]
        frame.addFromList(story,c)

        c.showPage() # Organisatiecultuur
        c.showPage()
        c.showPage()
        c.showPage()

        c.save()

        self.save_canvas(self.out_pdf_file,
                         existing_pdf)