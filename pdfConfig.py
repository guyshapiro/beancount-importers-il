import sys, os
# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

import beancountIsracard
import beancountFibi
import beancountCal

def categorizer(row):
    return "Expenses:Unknown"

def supermarketCategorizer(row):
    return "Expenses:Supermarket"

CONFIG = [
        beancountIsracard.Importer("Liabilities:Isracard:MC", "ILS",
            categorizer = categorizer),
        beancountCal.Importer("Liabilities:CAL:Sal", "ILS",
            categorizer = supermarketCategorizer),
        beancountFibi.Importer("Assets:Otzar:Checking", "ILS",
            categorizer = None)
]
