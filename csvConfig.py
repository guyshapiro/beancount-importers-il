
from beancount.ingest.importers import csv
from beancount.core import data
Col = csv.Col

def categorizer(txn):
    posting = data.Posting("Expenses:Unknown", None, None, None, None, None)
    txn.postings.append(posting)
    return txn

CONFIG = [
        csv.Importer({Col.DATE: 'Date',
            Col.AMOUNT_DEBIT: 'Amount',
            Col.PAYEE: 'Payee'},
            "Liabilities:Isracard:Card", "ILS",
            categorizer = categorizer,
            dateutil_kwds = {'dayfirst': True, 'yearfirst': False})
]
