#!/usr/bin/env python
# coding: utf-8

import pdfplumber
from bidi.algorithm import get_display as bidiFlip
import re


def verify(path):
    pdf = pdfplumber.open(path)
    page = pdf.pages[0]
    text = bidiFlip(page.extract_text(x_tolerance=1))
    ID_TEXT1 = "דף חשבון מספר"
    ID_TEXT2 = "להלן פירוט תנועות בחשבון לתקופה"
    return (ID_TEXT1 in text) and (ID_TEXT2 in text)


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


def getHlines(page, is_first_page=True, is_last_page=False):
    words = page.extract_words(x_tolerance=1)
    amounts = [word for word in words if AMOUNT_RE.match(word["text"])]
    text_height = amounts[0]['bottom'] - amounts[0]['top']
    tops = sorted(set(x['top'] for x in amounts))
    # the first amount in the first page is not part of the table
    if is_first_page:
        tops = tops[1:] 
    # the last amount in the last page is actually the prime interest rate
    if is_last_page:
        tops = tops[:-1]
    bottom_border = tops[-1] + (2*text_height)
    return tops + [bottom_border]

vlines = (42,101,168,216,263,501,540)

def visualDebug(page, is_first_page=True, is_last_page=False):
    im = page.to_image()
    hlines = getHlines(page, is_first_page, is_last_page)
    return im.draw_hlines(hlines).draw_vlines(vlines)

def extractPageData(page, is_first_page=True, is_last_page=False):
    hlines = getHlines(page, is_first_page, is_last_page)
    settings = {"horizontal_strategy":"explicit",
        "explicit_horizontal_lines":hlines,
        "explicit_vertical_lines":vlines}
    tables = page.debug_tablefinder(settings)
    return tables.tables[0].extract(x_tolerance=1)

def getPdfData(path):
    """
    Extract the raw table data from the PDF file
    """
    pdf = pdfplumber.open(path)
    res = []
    last_index = len(pdf.pages) - 1
    for index, page in enumerate(pdf.pages):
        res.extend(extractPageData(page, index==0, index==last_index))
    return res

def mapNoneItemsToEmpty(items):
    return map(lambda x: x if (x != None) else "", items)

DETAILS_RE = re.compile("(.\..\. )?(.*)(\(\d+\/\d+\/\d+\))")
def fixData(table):
    """Take the raw table data and fix its ordering"""
    res = []
    last_date = ""
    for row in table:
        row.reverse() # order the cells from right to left
        row = mapNoneItemsToEmpty(row)
        row = list(map(bidiFlip, row))

        # The different details fields share the same column in the PDF.
        # Replace the details string column with separated details fields
        details_str = row[1].replace("\n","")
        match = DETAILS_RE.match(details_str)
        if match == None:
            raise Exception("no match for {}".format(details_str))
        details = match.groups()
        
        details = mapNoneItemsToEmpty(details)
        row[1:2] = details

        # add date field for non-first rows of a day
        if row[0]:
            last_date = row[0]
        else:
            row[0] = last_date

        res.append(row)
    return res

