import os
from celery import shared_task
from celery import Celery
from celery.utils.log import get_task_logger

app = Celery()

os.environ['DJANGO_SETTINGS_MODULE'] = "travel_agency.settings"
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

logger = get_task_logger(__name__)


@shared_task(name='train_doc2vec', ignore_results=True)
def train_doc2vec():
    from ecommerce.utils.recommendation_scripts.Doc2VecHelper import train_doc2vec
    train_doc2vec()


@shared_task(name='train_item2vec', ignore_results=True)
def train_item2vec():
    from ecommerce.utils.recommendation_scripts.Item2VecHelper import train_item2vec
    train_item2vec()


@shared_task(name='train_rnn', ignore_results=True)
def train_rnn():
    from ecommerce.utils.recommendation_scripts.RnnHelper import train_rnn
    train_rnn()


@shared_task(name='find_popular_items', ignore_results=True)
def find_popular_items():
    from ecommerce.utils.helper_scripts.DatabaseOperations import find_popular_items
    find_popular_items(filter_date=750)
