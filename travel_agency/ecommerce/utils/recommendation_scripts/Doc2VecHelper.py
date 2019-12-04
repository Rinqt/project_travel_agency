import datetime
import django
import gensim
import logging
import os
import numpy as np
import pandas as pd
import pickle
from ecommerce.utils.helper_scripts.pre_process import clean_text
from nested_lookup import nested_lookup
from django.db.models import Count
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from ecommerce.utils.helper_scripts.DatabaseOperations import save_model, load_model, change_active_model
from ecommerce.utils.helper_scripts.Utils import concat_item_attributes

# Django Settings to use Doc2VecHelper.py file.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travel_agency.settings")


def train_doc2vec():
    """
    :summary:Train and save Doc2Vec Model.
    :workflow: Convert nested item dictionary to dataframe.
               Clean the text and merge the tokens into one row.
               Use the clean text dataframe and create corpus to train Doc2Vec Model.
               Create a Doc2Vec model and build a vocabulary by using the corpus.
               Save Doc2Vec Model and Vocabulary.
               (Important) Create items.pickle file. Since we need to have doc_vectors to find similar items, I need
               to keep them somewhere. I choose to keep them in binary format (JSON was causing precision loss in
               floats) since it is protection precision with out any data loss.
                    --> Pickle structure as follows:
                         { 'index': { 'doc_tag' : [doc_vector, words] } }

    :return: None since we are saving the Doc2Vec Model
    """
    item_dictionary = create_item_dictionary()
    temp_df = pd.DataFrame.from_dict(item_dictionary, orient='index')

    # Combine every column into one, separating by comma
    result_df = temp_df.apply(lambda x: ','.join(x.astype(str)), axis=1)

    # Pre-Process the text
    result_df = clean_text(result_df)

    train_corpus = list(read_corpus(result_df))

    model = Doc2Vec(vector_size=120, min_count=0, epochs=256)
    logging.warning('Doc2Vec model is completed!')

    model.build_vocab(train_corpus)
    logging.warning('Vocabulary build is completed!')

    model.train(train_corpus, total_examples=model.corpus_count, epochs=model.epochs)
    logging.warning('Doc2Vec model training is completed!')

    model_name = 'doc2vec__{date:%Y%m%d_%H-%M-%S}__.model'.format(date=datetime.datetime.now())
    vocabulary_name = 'vocabulary__{date:%Y%m%d_%H-%M-%S}__.voc'.format(date=datetime.datetime.now())

    model_pickle = pickle.dumps(model)
    vocabulary_pickle = pickle.dumps(model.vocabulary)

    save_model('d2v', model_name, model_pickle)
    save_model('d2v_vocabulary', vocabulary_name, vocabulary_pickle)

    logging.warning('Doc2Vec Model is saved in DB!!')
    logging.warning('Doc2Vec Vocabulary is saved in DB!!')

    pickle_dict = {}
    for index, sentence in enumerate(train_corpus):
        doc2vec_index = index

        pickle_dict[doc2vec_index] = {}

        doc_tag = int(sentence.tags[0])
        doc_vectors = model.docvecs[index]
        doc_words = sentence.words[:10]

        pickle_dict[index][doc_tag] = [doc_vectors, doc_words]

    items_pickle = pickle.dumps(pickle_dict)
    save_model('items', 'items_pickle', items_pickle)
    logging.warning('items.pickle is saved in DB!!')


def create_item_dictionary():
    """
    :summary: Creates a dictionary that contains item id, item attributes and item values.
    :workflow: Gather all destinations from database. (Since we have multiple attribute - value entry per destination
               it get distinct count to use later.
               Loop through every distinct destination we have.
               Create individual items by filtering object ids from destination
               Then, loop through every attribute that destination has and merge attributes with attributes,
                    values with values by separating them by #.
                        --> Dictionary structure as follows:
                            { 'item_id' : 'id'       :'1'
                                          'attribute':'att1#att2#att3#att4#',
                                          'value'    :'val1#val2#val3#val4#'
    :return: dictionary
    """
    from django.apps import apps
    Item = apps.get_model('ecommerce', 'Item')

    all_destination = Item.objects.values('object_id').annotate(the_count=Count('object_id'))

    item_dict = {}

    for destination in all_destination:
        individual_item = Item.objects.filter(object_id=destination['object_id'])
        item_dict[destination['object_id']] = concat_item_attributes(individual_item)

    res_dict = process_dictionary(item_dict)
    return res_dict


def process_dictionary(item_dictionary):
    """
    :summary: Create a multi dictionary which represents items and their attributes
    :workflow: Iterate through passed dictionary.
               Split item attributes and values by '#' symbol and put them into corresponding lists. (Note that,
               there will be always # at the end of the strings thus it will be replaced by ''. That is why,
               remove the last element of lists.
               Iterate the lists together and insert the data into dictionary.
                    --> Dictionary structure as follows:
                            {'dict1': {'innerkey': 'value'}} -> {
                                                                '1': {'att1':'val1',
                                                                      'att2':'val2',}}
                                                                      'att3':'val3',}}
                                                                }
    :param item_dictionary: Takes a dictionary that is structured as in create_item_dictionary()
    :return: Dictionary
    """
    items_dict = {}

    for key, value in item_dictionary.items():
        items_dict[key] = {}

        # Create an item object and split the attributes
        item = item_dictionary[key]
        item_attributes = item['attribute'].split('#')
        item_values = item['value'].split('#')

        # Delete last elements of the lists since it will always be empty. Because of the last # symbol
        del item_attributes[-1]
        del item_values[-1]

        for item_attribute, item_value in zip(item_attributes, item_values):
            items_dict[key][item_attribute] = item_value

    return items_dict


def find_vector_representation(_item_id, _items):
    """
    :param _item_id: item id that we want to find similar items.
    :param _items: entire item list
    :return: Vector Representation of the item
    """
    return nested_lookup(_item_id, _items)


def doc2vec_calculate_similarity(_item_id):
    """
    :summary: Find the 'topn' similar items.
    :workflow: Check if there is a saved Doc2Vec Model
               Load the 'items.pickle'.
               Find the vector representation of the _item_id by using find_vector_representation() function.
               Note that vector representation must be converted to numpy array before being sent to the model.
               Find the similar items.
               Get the similar doc ids and find the corresponding item ids.

    :param _item_id: item id that we want to find similar items.
    :return: list of recommended_items, none if nothing found
    """

    # TODO: Should I check if the model is in DB?

    model_binary = load_model('d2v', name=None)
    model = pickle.loads(model_binary[0])
    logging.warning('Doc2Vec Model is loaded.')

    # Find the item_id in items_pickle
    items_binary = load_model('items', 'items_pickle')
    items = pickle.loads(items_binary[0])
    logging.warning('Items are loaded.')

    selected_item_vector = find_vector_representation(_item_id, items)
    selected_item_vector = selected_item_vector[0][0]
    selected_item_vector = np.asarray(selected_item_vector)

    similar_items = model.docvecs.most_similar([selected_item_vector], topn=10)

    item_id_list = []
    for sim_item in similar_items:
        item_id_list.append(sim_item[0])

    temp = []
    for ids in item_id_list:
        if ids in items.keys():  # To make sure if the similar item is in the dictionary
            temp.append(items[ids])

    recommended_items = []
    for ids in temp:
        for rec_id in ids:
            recommended_items.append(rec_id)

    # Uncomment below 2 lines for evaluation
    #from ecommerce.utils.helper_scripts import evaluation
    #evaluation.evaluate_recommendations(_item_id, recommended_items[1:], 'd2v')

    return recommended_items


def read_corpus(df):
    """
    :summary: Tag the documents to be used in Doc2Vec Model Training.
    :param df: dataframe
    :return:
    """
    for i, line in enumerate(df):
        tokens = gensim.utils.simple_preprocess(line)
        item_id = df.index.values.astype(int)[i]
        yield TaggedDocument(tokens, [item_id])
