"""
Tests for the mergetools.py script.
"""
import tempfile
import random
from contextlib import contextmanager
import string
import datetime
import csv

import pandas as pd

import mergetools
from scraper import CSV_HEADERS

def random_str(length, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(length))

def random_fb_dataframe(size=100, until=datetime.datetime.now()):
    """Returns a random dataframe that looks a bit like the data we tend to
    get from facebook (and has the same columns) but with utterly random
    content. May not quite make sense as regards comments etc. Will have to
    ensure that it does before using for testing context."""
    # choose a random page name
    pagename = random_str(10)

    data = {
        "page":[pagename for _ in range(size)],
        "posted by":[random_str(10) for _ in range(size)],
        "message":[random_str(100, chars=string.ascii_lowercase + ' ')
                   for _ in range(size)],
        "link":[random_str(25) for _ in range(size)],
        "shares":[random.randint(0,15) for _ in range(size)],
        "likes":[random.randint(0,1000) for _ in range(size)],
        "number of comments":[random.randint(0,50) for _ in range(size)],
        "pic":['' for _ in range(size)],
        "url":[random_str(50) for _ in range(size)],
        "type":[random.choice(['post','comment','comment'])
                for _ in range(size)]
    }
    start_time = until - (datetime.timedelta(1) * size)
    frame = pd.DataFrame(
        data=data,
        # idces should be a date range
        index=pd.DatetimeIndex(start=start_time,
                               periods=size,
                               freq='D')
        #columns=CSV_HEADERS,
    )
    return frame

def setup_disjoint():
    """Make some fake, totally disjoint data. Returns 2 pandas DataFrames
    with the same columns and different data"""
    start_a = datetime.datetime.now()
    start_b = datetime.datetime.now() - datetime.timedelta(50)
    return (random_fb_dataframe(size=30, until=start_a),
            random_fb_dataframe(size=30, until=start_b))

@contextmanager
def write_dataframes(frames, encoding='utf-16'):
    """Writes a sequence of dataframes to temporary files and returns the
    filenames. Should be used as a context manager, will clean up after
    itself"""
    files = []
    for frame in frames:
        files.append(tempfile.NamedTemporaryFile(mode='w', delete=False))
        frame.to_csv(files[-1],
                     encoding=encoding,
                     index_label='dates',
                     quoting=csv.QUOTE_ALL,
                     sep='\t')
        # actually write it
        files[-1].close()
    # yield the names
    yield [f.name for f in files]
    # close the files
    for f in files:
        f.delete()

# no doubt someday it will make sense to have this very cleverly organised
# but right now there is only one functionality to test
class Symdiff_Test(object):
    """Tests for the symmetric difference with context op"""

    def disjoint_test(self):
        """Tests that the symmetric difference of two disjoint frames is
        just their union."""
        print('symdiff - testing disjoint')
        a,b = setup_disjoint()
        op = mergetools.SymmetricDifference(a,b,
                                            write_out=False,
                                            do_context=False)
        result_1 = pd.concat([a,b])
        result_2 = op()

        assert result_1.equals(result_2)

    def loadfile_test(self):
        """Make sure it can load data from file and perform an op without errors
        """
        print('symdiff - testing files')
        with write_dataframes(setup_disjoint()) as data:
            op = mergetools.SymmetricDifference.from_args(data)
            op()
