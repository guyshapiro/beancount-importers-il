
import collections.abc

from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core import data
from beancount.core.position import Cost

import dateutil.parser

import fibi

class Importer(importer.ImporterProtocol):
    "An importer for Fibi PDF files"

    def __init__(self, account_name, currency="ILS", categorizer=None):
        self.account = account_name
        self.currency = currency
        self.categorizer = categorizer

    def identify(self, f):
        if (not f.name.lower().endswith(".pdf")):
            return False
        return fibi.verify(f.name)

    def dateParse(self, s):
        return dateutil.parser.parse(s, dayfirst = True, yearfirst=False).date()


    def extract(self, f):
        entries = []
        path = f.name
        raw = fibi.getPdfData(path)
        table = fibi.fixData(raw)
        for index, row in enumerate(table):
            txn_date = self.dateParse(row[0])
            txn_payee = ""
            txn_desc = row[2]
            credit = D(row[5].rstrip('0').rstrip('.'))
            debit = D(row[6].rstrip('0').rstrip('.'))
            balance = D(row[7].rstrip('0').rstrip('.'))
            txn_amount = credit - debit

            meta = data.new_metadata(f.name, index)

            txn = data.Transaction(
                meta=meta,
                date=txn_date,
                flag=flags.FLAG_OKAY,
                payee=txn_payee,
                narration=txn_desc,
                tags=data.EMPTY_SET,
                links=data.EMPTY_SET,
                postings=[])

            txn.postings.append(
                    data.Posting(
                        self.account,
                        amount.Amount(txn_amount, self.currency),
                        None, None, None, None)
                    )

            txn_account = None
            if isinstance(self.categorizer, collections.abc.Callable):
                txn_account = self.categorizer(row)

            if txn_account:
                txn.postings.append(
                        data.Posting(
                            txn_account,
                            None,
                            None, None, None, None)
                        )

            entries.append(txn)

        return entries
