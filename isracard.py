#!/usr/bin/env python
# coding: utf-8

import pdfplumber
import decimal
from bidi.algorithm import get_display as bidiFlip

def verify(path):
    pdf = pdfplumber.open(path)
    page = pdf.pages[0]
    text = bidiFlip(page.extract_text(x_tolerance=1))
    ID_TEXT1 = "www.isracard.co.il"
    return (ID_TEXT1 in text)


def getPdfData(path):
    """
    Extract the raw table data from the PDF file
    """
    pdf = pdfplumber.open(path)
    page = pdf.pages[0]
    # The lines in the table are images with original height of 3 pixels
    lines = list(filter(lambda x: x['srcsize'][1] == 3, page.images))
    line_tops = sorted(img['top'] for img in lines)

    D = decimal.Decimal
    avg_height = round((line_tops[-1] - line_tops[0])/(len(line_tops)-1), 3)
    # Before we use the average table raw height, verify if it's meaningful
    for (y0, y1) in zip(line_tops, line_tops[1:]):
        height = y1 - y0
        if (height > avg_height*D(1.2)):
            print("Warning: tall row on top={} height is {}, average is {:.3}".format(y0, height, avg_height))
        if (height < avg_height*D(0.8)):
            print("Warning: short row on top={} height is {}, average is {:.3}".format(y0, height, avg_height))
    # The first separation line is below the first raw. The table start above it.
    table_top = line_tops[0] - decimal.Decimal(avg_height)
    # Same for the last raw
    table_bottom = line_tops[-1] + decimal.Decimal(avg_height)

    crop = page.crop((lines[0]['x0'], table_top, lines[0]['x1'], table_bottom))

    settings = {"vertical_strategy":"text", "explicit_horizontal_lines":[table_top]+line_tops+[table_bottom]}
    tables = crop.debug_tablefinder(settings)
    return tables.tables[0].extract(x_tolerance=1)

def fixData(table):
    """Take the raw table data and fix its ordering"""
    res = []
    for row in table:
        row.reverse() # order the cells from right to left
        row = map(lambda x: x if (x != None) else "", row)
        row = list(map(bidiFlip, row))

        res.append(row)
    return res

