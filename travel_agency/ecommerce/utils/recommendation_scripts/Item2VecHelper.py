import datetime
import django
import logging
import os
import pickle
import pandas as pd

from gensim.models.word2vec import Word2Vec
from ecommerce.utils.helper_scripts.DatabaseOperations import save_model, load_model, get_all_user_sequences

# Django Settings to use Item2VecHelper.py file.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travel_agency.settings")
#django.setup()
logger = logging.getLogger(__name__)


def train_item2vec():
    """
    :summary:  Train and save item2vec Model.
    :workflow: In order to use items as "words" we need to find user sequences. Currently, this is done by using
               pandas. First, data must be grouped by user ids. Then, we need to have user sequences for individual
               users to put each item which is belong to that user.
               After creating the sequences, we can use the sequence data to feed item2vec model. Since item2vec
               is same as working with word2vec, (instead of words, we have items and instead of sentences, we have
               user sequences) we will just give user items in the sequence to train our model.

    :return: Model is saved to database
    """
    sequences = get_all_user_sequences()
    user_sequence_df = pd.DataFrame.from_records(sequences, columns=['object_id', 'user_sequence'])
    items_in_sequence = user_sequence_df

    train_data = items_in_sequence['user_sequence'].values.tolist()

    logging.info('Training is started...')
    model = Word2Vec(train_data, min_count=0, size=120, workers=8, window=1, sg=0, iter=512)

    model_name = 'item2vec__{date:%Y%m%d_%H-%M-%S}__.model'.format(date=datetime.datetime.now())
    model_pickle = pickle.dumps(model)

    save_model('i2v', model_name, model_pickle)
    logging.info('Item2Vec Model is saved in DB!!')


def item2vec_calculate_similarity(_item_id):
    """
    :summary:  Creates a recommendation list that contains ids of the item that is similar to given id.
    :workflow:
                -> Load the item2vec model from database.
                -> Use model to find similar items to given item id.
                -> Create a recommendation list and start appending predicted item ids (Note that some item ids
                   might not be in the database)
                -> Return the list.

    :return: recommended_items_set: List of item ids to use for recommendation
    """
    from ecommerce.utils.helper_scripts.DatabaseOperations import find_object_id

    model_binary = load_model('i2v', name=None)
    model = pickle.loads(model_binary[0])
    logging.warning('Item2Vec model is loaded.')

    similar_items = model.most_similar(str(_item_id))

    temp_recommended_items = []
    for rec_item in similar_items:
        temp_recommended_items.append(rec_item[0])

    recommended_items_set = []
    for item_id in temp_recommended_items:
        res = find_object_id(item_id)
        if res is 1:
            recommended_items_set.append(int(item_id))

    # Uncomment below 2 lines for evaluation
    #from ecommerce.utils.helper_scripts import evaluation
    #evaluation.evaluate_recommendations(_item_id, recommended_items_set, 'i2v')

    return recommended_items_set
