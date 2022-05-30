from classes.PDF import *
import sys
sys.path.append('../functions')
from functions.function import *
import numpy as np

class Education(PDF):
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

    def create_canvas(self):
        font_folder = str(Path("", "fonts"))
        pdfmetrics.registerFont(TTFont('Montserrat-SemiBold', Path(font_folder,'Montserrat-SemiBold.ttf')))

        score_percentages = self.calculate_final_scores(self.person,
                                                        self.variables_in_order)

        report_filename, pages, txt, vars_for_text = self.choose_report_filename(score_percentages)

        c, existing_pdf = self.prep_pdf(report_filename, pages)
        c.showPage()
        for i in range(len(self.offset_vertical)):
            self.draw_score(c,
                            self.score_offset[i],
                            self.offset_horizontal[i],
                            score_percentages[i],
                            self.offset_vertical[i],
                            height = 42)

        textobject = c.beginText(1.9*cm, 6.6*cm)
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

        if "autonomie" in remaining_vars:
            pages.remove(autonomie_page)

        if "relatie" in remaining_vars:
            pages.remove(relatie_page)

        if "competentie" in  remaining_vars:
            pages.remove(competentie_page)

        print(score_percentages)
        print(pages)

        # This code compares the original list with the list of remaining vars and keeps the non-intersecting vars
        vars_for_text = list(set(remaining_vars).symmetric_difference(self.variables_in_order))

        txt = ""
        cnt = 0
        for var in range(len(vars_for_text)):
            if cnt == 0:
                txt += vars_for_text[var]
            elif cnt == 1:
                txt += ", " + vars_for_text[var]
            elif cnt == 2:
                txt += " en " + vars_for_text[var]

            cnt += 1

        results_text = f"""Uit de resultaten blijkt dat je ontwikkelingspotentie het grootst is \nop het gebied van {txt}. \nOp de volgende pagina kun je alvast wat informatie en tips \nvinden om zelf aan de slag te gaan met het ondersteunen \nvan {txt}.
        """

        return report_filename, pages, results_text, vars_for_text