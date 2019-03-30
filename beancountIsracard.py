
import collections.abc

from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core import data
from beancount.core.position import Cost

import dateutil.parser

import isracard

class Importer(importer.ImporterProtocol):
    "An importer for Isracard PDF files"

    def __init__(self, account_name, currency="ILS", categorizer=None):
        self.account = account_name
        self.currency = currency
        self.categorizer = categorizer

    def identify(self, f):
        if (not f.name.lower().endswith(".pdf")):
            return False
        return isracard.verify(f.name)

    def dateParse(self, s):
        return dateutil.parser.parse(s, dayfirst = True, yearfirst=False).date()


    def extract(self, f):
        entries = []
        path = f.name
        raw = isracard.getPdfData(path)
        table = isracard.fixData(raw)
        for index, row in enumerate(table):
            try:
                txn_date = self.dateParse(row[0])
            except ValueError:
                print("; error parsing date '{}', skipping".format(row[0]))
                continue

            txn_payee = row[2]
            txn_amount = D(row[4].rstrip('0').rstrip('.'))
            txn_payment = D(row[5].rstrip('0').rstrip('.'))
            if txn_amount != txn_payment:
                txn_desc = "payment {:.2}/{:.2}".format(txn_payment,txn_amount)
            else:
                txn_desc = None

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
                        amount.Amount(-1*txn_amount, self.currency),
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
