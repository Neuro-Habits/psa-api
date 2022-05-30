from classes.PDF import *
import sys
sys.path.append('../functions')
from functions.function import *


class Vitality(PDF):
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
        score_percentages = self.calculate_final_scores(self.person,
                                                        self.variables_in_order)

        report_filename = self.choose_report_filename(score_percentages)

        pages = list(range(8))

        c, existing_pdf = self.prep_pdf(report_filename, pages)
        c.showPage()
        for i in range(len(self.offset_vertical)):
            self.draw_score(c,
                            self.score_offset[i],
                            self.offset_horizontal[i],
                            score_percentages[i],
                            self.offset_vertical[i])

        c.showPage()
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

        if score_percentages[0] <= percentage_from_score(self.min_score, self.max_score, 3):
            report_filename = "quickscan_green"
        elif score_percentages[0] <= percentage_from_score(self.min_score, self.max_score, 7):
            report_filename = "quickscan_yellow"
        else:
            report_filename = "quickscan_red"

        return report_filename