import pandas as pd
import numpy as np
import datetime


def popular_item_list_generator(user_data):
    df = pd.DataFrame(user_data, columns=['pk', 'user_id', 'item_id', 'ts'])
    df['times_clicked'] = df.groupby('item_id')['item_id'].transform('count')
    df = df.drop_duplicates(subset=['item_id'], keep='first')

    df = df.sort_values(by=['times_clicked'])
    df['ts'] = pd.to_datetime(df['ts'], dayfirst=True)

    pop_item_list = list(df['item_id'].tail(6))
    return pop_item_list


def load_dataset(_path):
    dataset = pd.read_csv(_path, sep=';', low_memory=False)
    columns = ['userID', 'objectID', 'lastModified']
    dataset.columns = columns

    dataset[['userID', 'objectID']] = dataset[['userID', 'objectID']].astype(str)
    dataset['lastModified'] = pd.to_datetime(dataset['lastModified'], format='%d/%m/%Y %H:%M').dt.normalize()

    #dataset = create_sessions(dataset)
    return dataset


def load_user_data():
    from ecommerce.utils.helper_scripts.DatabaseOperations import get_user_data
    user_data = get_user_data()

    column_names = ['pk', 'user_id', 'item_id', 'ts']
    user_data_df = pd.DataFrame(user_data, columns=column_names)

    #user_data_df.to_csv('allstuff.csv', sep='\t', encoding='utf-8')

    # Convert 'string' date to Datetime
    user_data_df['ts'] = pd.to_datetime(user_data_df['ts'], dayfirst=True)

    # Remove Primary Key Column
    del user_data_df['pk']

    return user_data_df


def create_sequences(df):
    user_data_df = df.groupby(['user_id', 'ts'], as_index=False).agg(lambda x: x)

    user_data_df = create_sequence_ids(user_data_df)

    # group by session id and concat song_id
    groups = user_data_df.groupby('sequence_id')

    # convert item ids to string, then aggregate them to lists
    aggregated = groups['item_id'].agg({'sequence': lambda x: list(map(str, x))})
    init_ts = groups['ts'].min()
    users = groups['user_id'].min()  # it's just fast, min doesn't actually make sense

    result = aggregated.join(init_ts).join(users)
    result.reset_index(inplace=True)

    return result


def create_sequence_ids(df):
    temp = pd.DataFrame(columns=['sequence_id', 'user_id', 'item_id', 'ts'])

    session_counter = 1
    prev_time_step = df['ts'][0]

    for index, row in df.iterrows():
        if (row['ts'] - prev_time_step > pd.Timedelta(30, unit='d')) or (
                row['ts'] - prev_time_step <= pd.Timedelta(-1, unit='d')):
            session_counter += 1

        prev_time_step = row['ts']
        data = {'sequence_id': session_counter, 'user_id': row['user_id'], 'item_id': row['item_id'], 'ts': row['ts']}
        temp = temp.append(data, ignore_index=True)

    temp['ts'] = temp.ts.apply(lambda x: (x - datetime.datetime(1970, 1, 1)).total_seconds())

    return temp


def last_session_out_split(data,
                           user_key='user_id',
                           session_key='sequence_id',
                           time_key='ts'):
    """
    Assign the last session of every user to the test set and the remaining ones to the training set
    """
    sessions = data.sort_values(by=[user_key, time_key]).groupby(user_key)[session_key]
    last_session = sessions.last()
    train = data[~data.sequence_id.isin(last_session.values)].copy()
    test = data[data.sequence_id.isin(last_session.values)].copy()
    return train, test


def split_dataset():
    """
    Assign the last session of every user to the test set and the remaining ones to the training set
    """
    from ecommerce.utils.helper_scripts.DatabaseOperations import get_user_data, get_all_user_sequences

    user_data = get_all_user_sequences()
    columns_names = ['user_id', 'sequence']
    user_data_df = pd.DataFrame(user_data, columns=columns_names)
    user_data_df['session_id'] = user_data_df.groupby(['user_id']).ngroup()

    train = 1
    test = 2

    train = user_data_df.copy()
    train = train.iloc[:100]
    test = pd.DataFrame(columns=columns_names)

    for index, row in train.iterrows():
        temp = [{'user_id': row['user_id'], 'sequence': row['sequence'][-1]}]
        test = test.append(temp, ignore_index=True)
        train['sequence'][index] = train['sequence'][index][:-1]

    return train, test


def dataset_to_gru4rec_format(dataset):
    """
    Convert a list of sequences to GRU4Rec format.
    Based on this StackOverflow answer: https://stackoverflow.com/a/48532692

    :param dataset: the dataset to be transformed
    """

    lst_col = 'sequence'
    df = dataset.reset_index()
    unstacked = pd.DataFrame({
        col: np.repeat(df[col].values, df[lst_col].str.len()) for col in df.columns.drop(lst_col)}
    ).assign(**{lst_col: np.concatenate(df[lst_col].values)})[df.columns]
    # ensure that events in the session have increasing timestamps
    unstacked['ts'] = unstacked['ts'] + unstacked.groupby('user_id').cumcount()
    unstacked.rename(columns={'sequence': 'item_id'}, inplace=True)
    return unstacked


def remove_stop_words(_s):
    from stop_words import get_stop_words
    from string import punctuation
    import re

    stop_words = get_stop_words('czech')

    _s = ' '.join(word for word in _s.split() if word not in (stop_words and punctuation))

    punctuation = r"""!"#$%&'()*+-./:;<=>?@[\]^_`{|}~"""  # Remove comma from the default set
    table = str.maketrans(dict.fromkeys(punctuation))
    new_s = _s.translate(table)

    # Remove the html tags
    cleaned_s = re.sub('<[^<]+?>', '', new_s)
    return cleaned_s


def clean_text(df):
    df_clean = pd.DataFrame({'clean': df})
    df_clean.loc[:, "clean"] = df_clean.clean.apply(lambda x: str.lower(x))
    df_clean.loc[:, "clean"] = df_clean.clean.apply(lambda x: remove_stop_words(x))

    df = df_clean["clean"]
    return df
