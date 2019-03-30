#!/usr/bin/env python
# coding: utf-8

import pdfplumber
from bidi.algorithm import get_display as bidiFlip
import re


def verify(path):
    pdf = pdfplumber.open(path)
    page = pdf.pages[0]
    text = bidiFlip(page.extract_text(x_tolerance=1))
    ID_TEXT1 = "מידע עבור כרטיס ויזה"
    ID_TEXT2 = "Cal"
    return (ID_TEXT1 in text) and (ID_TEXT2 in text)

# PDF extraction helpers
def process_line_chars(chars, x_tolerance):
    x0, top, x1, bottom = pdfplumber.utils.objects_to_bbox(chars)
    return {
        "x0": x0,
        "x1": x1,
        "top": top,
        "bottom": bottom,
        "text": pdfplumber.utils.collate_line(chars, x_tolerance)
    }

def extract_lines(chars, x_tolerance, y_tolerance):
    "Extract text lines from the PDF, with position information on each line"
    doctop_clusters = pdfplumber.utils.cluster_objects(chars, "doctop", y_tolerance)
    return [process_line_chars(line_chars, x_tolerance) for line_chars in doctop_clusters]

# End of healpers

AMOUNT_RE = re.compile(r"\d{1,3}(,\d{3})*\.\d{2}$")
def test_amount_re():
    tests = """11
    11.00
    11.1
    123,123.01
    1,123.00
    1,13.00
    123,123,123.00
    1,1,1.00
    105-012345
    18.00%""".split()
    return [test for test in tests if AMOUNT_RE.match(test)]


def cropTable(page):
    "Crop the main table from the PDF"
    y_tolerance=3
    x_tolerance=1

    lines = extract_lines(page.chars, x_tolerance, y_tolerance)
    HEAD_TEXT = "פירוט עסקות שנצברו"
    SUM_TEXT = 'סה"כ לתאריך'

    table_top = [ line for line in lines if HEAD_TEXT in bidiFlip(line['text']) ][0]['bottom']
    table_bottom = [ line for line in lines if SUM_TEXT in bidiFlip(line['text']) ][0]['bottom']

    # add one point to the table_top position to avoid catching the header text in the data table
    return page.crop((0, table_top+1, page.width, table_bottom))

def getVlines(crop):
    x_cords = [e['x0'] for e in crop.edges]
    vlines = [c['x0'] for c in crop.curves] + [max(x_cords), min(x_cords)]
    return vlines


def extractPageData(page):
    crop = cropTable(page)
    vlines = getVlines(crop)
    settings = {"horizontal_strategy":"lines",
                "vertical_strategy":"explicit",
                "explicit_vertical_lines":vlines}
    tables = crop.debug_tablefinder(settings)
    return tables.tables[0].extract(x_tolerance=1)

def getPdfData(path):
    """
    Extract the raw table data from the PDF file
    """
    pdf = pdfplumber.open(path)
    page = pdf.pages[0]
    return extractPageData(page)

def stripILS(text):
    "Remove the ILS symbol from the amount string"
    return text.strip("₪").strip()

def fixData(table):
    """Take the raw table data and fix its ordering"""
    res = []
    # skip the titles and the summery lines
    table = table[1:-1]
    for row in table:
        row.reverse() # order the cells from right to left
        row = list(map(bidiFlip, row))
        row[5] = stripILS(row[5])
        row[6] = stripILS(row[6])
        res.append(row)
    return res

