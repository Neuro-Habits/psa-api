from classes.PDF import *
import sys
import numpy as np

sys.path.append('../functions')
from functions.function import *
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import Color

custom_style = ParagraphStyle('custom_style',
                              fontName="Montserrat-Medium",
                              fontSize=10,
                              textColor=Color(0, 0, 0, 1)
                              )


class Education(PDF):
    def __init__(self,
                 attrs,
                 person=None):

        self.attrs = attrs
        self.variables_in_order = ['Autonomie', 'Controle', 'Competentie', 'Relatie']

        for k, v in self.attrs.items():
            setattr(self, k, v)

    def init_super(self):
        PDF.__init__(self,
                     self.attrs,
                     person=self.person
                     )

    def create_scores_list(self,
                           person,
                           variables):

        scores_list = []
        for variable in variables:
            print(variable)
            scores_list.append(getattr(person, variable))

        return scores_list

    def create_canvas(self):
        x_leftAlign = -(self.doc_center / 2)
        font_folder = str(Path("", "fonts"))
        pdfmetrics.registerFont(TTFont('Montserrat-SemiBold', Path(font_folder,'Montserrat-SemiBold.ttf')))

        score_percentages = np.array([])
        for i in range(len(self.variables_in_order)): # For every variable
            subject = self.variables_in_order[i]
            sub_attrs = self.page_attrs[subject]

            perc = percentage_from_score(sub_attrs['min_score'],sub_attrs['max_score'], getattr(self.person, subject), rotate=True)
            print(f"Percentage for score {subject}: {perc}")

            score_percentages = np.append(score_percentages, perc)

        report_filename, pages, txt, vars_for_text = self.choose_report_filename(score_percentages)

        c, existing_pdf = self.prep_pdf(report_filename, pages)
        c.showPage()

        for i in range(len(self.variables_in_order)):
            sub_attrs = self.page_attrs[self.variables_in_order[i]] # Page attributes of current subject

            self.draw_score(c,
                            sub_attrs['score_offset'],
                            x_leftAlign + sub_attrs['offset_horizontal'],
                            score_percentages[i],
                            sub_attrs['offset_vertical'],
                            height=42)

        textobject = c.beginText(1.9*cm, 6*cm)
        textobject.setFont('Montserrat-SemiBold', 13)
        textobject.setFillColorRGB(34/255,34/255,34/255)

        for line in txt.splitlines(False):
            textobject.textLine(line.rstrip())

        c.drawText(textobject)
        c.showPage()

        for i in range(len(vars_for_text)):
            c.showPage()

        c.showPage()
        c.showPage()
        c.showPage()
        c.showPage()
        c.showPage()
        c.save()

        self.save_canvas(self.out_pdf_file,
                         existing_pdf)

    def choose_report_filename(self,
                               score_percentages):

        report_filename = "Quickscan onderwijs (COMPLEET)"
        pages = list(range(0,10))

        autonomie_page = 2
        relatie_page = 3
        competentie_page = 4

        # Get indices of scores with max values
        M = [i for i, x in enumerate(score_percentages) if x == max(score_percentages)]

        remaining_vars = np.array(self.variables_in_order)

        # Values which are still in the 'remaining_vars' list are the ones with min scores
        # Min score = sufficient score for this subject and thus should be removed

        # Max pages should be kept
        remaining_vars = np.delete(remaining_vars, M)
        print("Vars to be removed:")
        print(remaining_vars)

        if "Autonomie" in remaining_vars and "Controle" in remaining_vars:
            pages.remove(autonomie_page)

        if "Relatie" in remaining_vars:
            pages.remove(relatie_page)

        if "Competentie" in remaining_vars:
            pages.remove(competentie_page)

        print(score_percentages)
        print(pages)

        # This code compares the original list with the list of remaining vars and keeps the non-intersecting vars
        # vars_for_text = list(set(remaining_vars).symmetric_difference(self.variables_in_order))
        vars_for_text = [i for i in self.variables_in_order if i not in remaining_vars]
        print("Vars for text")
        print(vars_for_text)

        txt = ""
        cnt = 0
        total_vars = len(vars_for_text)

        for var in range(total_vars):
            if cnt == 0:
                txt += vars_for_text[var]
            elif cnt == 1 or cnt == 2:
                if total_vars == 2:
                    txt += " en " + vars_for_text[var]
                else:
                    txt += ", " + vars_for_text[var]
            elif cnt == 3:
                txt += ", en " + vars_for_text[var]

            cnt += 1

        add_text = None
        txt = txt.lower()
        txt_end = txt

        if 'controle' in txt:
            add_text = "Controle is een specifiek onderwerp binnen autonomie.\n"

            txt_end = txt_end.replace(" en controle", "")
            txt_end = txt_end.replace(", controle,", ",")
            txt_end = txt_end.replace(", controle, en", " en")

        results_text = f"""Uit de resultaten blijkt dat je ontwikkelingspotentie het grootst is \nop het gebied van {txt}. \n{add_text}Op de volgende pagina kun je alvast wat informatie en tips \nvinden om zelf aan de slag te gaan met het ondersteunen \nvan {txt_end}.
        """

        return report_filename, pages, results_text, vars_for_text