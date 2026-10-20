"""The CSV dialect of the CourtListener bulk files.

They are written by PostgreSQL `COPY ... WITH (FORMAT csv, ESCAPE '\\')`, so a quote inside a field is escaped
as a backslash-quote, not doubled. Python's csv module defaults to doubling. Read with the default, the opinion
text fields -- full of HTML attributes like label=\\"394\\" -- split mid-field: a 315 MB sample of opinions
came back as 1,104,813 rows instead of 12,439, and a 400 MB sample of clusters silently lost 32 of 182,430
cases (about 1,800 across the snapshot), each of which would have looked like a case that does not exist.
Every reader of these files goes through here.
"""
import csv
import sys

csv.field_size_limit(sys.maxsize)
DIALECT = {"escapechar": "\\", "doublequote": False}


def reader(fh):
    return csv.DictReader(fh, **DIALECT)
