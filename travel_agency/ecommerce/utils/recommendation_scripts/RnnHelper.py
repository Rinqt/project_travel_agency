import datetime
import pickle
import logging
import numpy as np

from ecommerce.utils.helper_scripts.pre_process import dataset_to_gru4rec_format
from ecommerce.utils.helper_scripts.rnn.gru4rec import GRU4Rec
from ecommerce.utils.helper_scripts.DatabaseOperations import save_model, load_model, find_object_id


def train_rnn():

    recommender = RnnRecommender()
    recommender.parameters = recommender.set_parameters({'epochs': 250})
    recommender.create_training_data()

    # parse training data to GRU4Rec format
    recommender.train_data = dataset_to_gru4rec_format(dataset=recommender.train_data)

    recommender.model = GRU4Rec(layers=recommender.parameters['session_layers'],
                                n_epochs=recommender.parameters['epochs'],
                                batch_size=recommender.parameters['batch_size'],
                                learning_rate=recommender.parameters['learning_rate'],
                                momentum=recommender.parameters['momentum'],
                                dropout_p_hidden=recommender.parameters['dropout'],
                                session_key='sequence_id',
                                item_key='item_id',
                                time_key='ts')

    recommender.model.fit(recommender.train_data)

    model_name = 'rnn__{date:%Y%m%d_%H-%M-%S}__.model'.format(date=datetime.datetime.now())
    model_pickle = pickle.dumps(recommender.model)

    save_model('rnn', model_name, model_pickle)
    logging.warning('Rnn Model is saved in DB!!')


class RnnRecommender:
    def __init__(self):
        self.parameters = \
            {
                'session_layers': [5],
                'batch_size': 16,
                'learning_rate': 0.1,
                'momentum': 0.1,
                'dropout': 0.1,
                'epochs': 1,
            }

        self.pseudo_session_id = 0
        self.model = None
        self.train_data = None
        self.test_data = None

    def recommend(self, item_sequence):
        for item in item_sequence:
            pred = self.model.predict_next_batch(np.array([self.pseudo_session_id]),
                                                 np.array([item]),
                                                 batch=1)

        # sort items by predicted score
        pred.sort_values(0, ascending=False, inplace=True)
        # increase the psuedo-session id so that future call to recommend() won't be connected
        self.pseudo_session_id += 1
        # convert to the required output format
        return [([x.index], x._2) for x in pred.reset_index().itertuples()]

    def set_parameters(self, parameter_dict):
        """
        Method will set the parameters based on what they chose on model creation page.
        If user didn't select a parameter, it will be set to default value.

        :param parameter_dict: Parameters that user selected on model creation page
        """
        for key, value in parameter_dict.items():
            self.parameters[key] = value

        return self.parameters

    def create_training_data(self):
        from ecommerce.utils.helper_scripts.pre_process import load_user_data, create_sequences, last_session_out_split

        user_data_df = load_user_data()
        user_data_df = create_sequences(user_data_df)
        self.train_data, self.test_data = last_session_out_split(user_data_df)


def rnn_calculate_similarity(object_id):
    # TODO: Later we can give item sequences and get predictions based on the sequence not only for one item.
    # TODO: [cont.] Append items that user clicked and send the item list here
    rnn_recommender = RnnRecommender()
    model_binary = load_model('rnn', name=None)
    model = pickle.loads(model_binary[0])

    rnn_recommender.model = model
    temp_recommended_items = rnn_recommender.recommend(str(object_id))

    recommended_items_set = []
    for item_id in temp_recommended_items[:10]:
        res = find_object_id(item_id[0][0])
        if res is 1:
            recommended_items_set.append(item_id[0][0])

    # Uncomment below 2 lines for evaluation
    #from ecommerce.utils.helper_scripts import evaluation
    #evaluation.evaluate_recommendations(object_id, recommended_items_set, 'rnn')

    return recommended_items_set
