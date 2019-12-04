import sqlite3
import os.path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(BASE_DIR, "../db.sqlite3")

# ITEM QUERIES:
query_insert_item = ''' INSERT INTO ecommerce_item('object_id', 'attribute', 'value') VALUES(?, ?, ?); '''
query_delete_item = ''' DELETE FROM ecommerce_item WHERE object_id = ?; '''
query_update_item = ''' UPDATE ecommerce_item SET value = ? WHERE object_id = ? AND attribute = ?; '''
query_check_item  = ''' SELECT object_id FROM ecommerce_item WHERE object_id = ?;'''
query_user_items  = """ SELECT object_id FROM ecommerce_user WHERE user_id = ?; """

# USER QUERIES
query_check_user           = ''' SELECT user_id FROM ecommerce_user WHERE user_id = ?;'''
query_add_user             = ''' INSERT INTO ecommerce_user('user_id', 'object_id') VALUES(?, ?); '''
query_user_ids             = """ Select DISTINCT user_id FROM ecommerce_user; """
query_insert_user_sequence = """ INSERT INTO ecommerce_user_sequences('user_id', 'user_sequence') VALUES(?, ?); """
query_user_sequences       = ''' SELECT user_sequence FROM ecommerce_user_sequences WHERE user_id = ? GROUP BY user_sequence; '''
query_find_sequence_like   = ''' SELECT user_id, user_sequence FROM ecommerce_user_sequences WHERE user_sequence LIKE ? '''
query_all_sequence   = ''' SELECT user_id, user_sequence FROM ecommerce_user_sequences '''

# MODEL QUERIES
query_save_models      = ''' INSERT INTO ecommerce_recommender_model('identifier', 'name', 'created', 'model', 'active') VALUES(?, ?, ?, ?, ?); '''
query_latest_model     = ' SELECT model FROM ecommerce_recommender_model WHERE identifier = ? '
#query_latest_model     = " SELECT model FROM ecommerce_recommender_model WHERE identifier = ? AND active = " '\'' + "TRUE" + '\' '
query_given_model      = ''' SELECT model FROM ecommerce_recommender_model WHERE identifier = ? AND name = ? '''
query_deactivate_model =     """ UPDATE ecommerce_recommender_model SET active = """ + '\'' + 'FALSE' + '\'' + """ WHERE active = """ + '\'' + 'TRUE' + '\''
# query_activate_model =
query_insert_recommendation_performance = """ INSERT INTO performance_results('user_id', 'total_items', 'precision', 'recall', 'mrr', 'model') VALUES(?, ?, ?, ?, ?, ?); """


def save_model(identifier, name, model):
    """
    :param identifier: Recommender tag (e.g. 'i2v' , 'd2v')
    :param name: name of the model which is described in the model code
    :param model: binary representation of the model
    :return: Saves the model to database
    """
    conn = create_database_connection(db_path)

    import datetime
    curr_time = datetime.datetime.now()

    query = query_save_models

    data_set = (identifier, name, curr_time, model, 'FALSE')
    db_cursor = conn.cursor()
    db_cursor.execute(query, data_set)
    conn.commit()

    db_cursor.close()
    return db_cursor.lastrowid


def load_model(identifier, name=None):
    """
    If model name is not given, the latest model will be loaded.
    :param identifier: Recommender tag (e.g. 'i2v' , 'd2v')
    :param name: name of the model which is described in the model code
    :return: Loads the model from database
    """
    conn = create_database_connection(db_path)

    if name is None:
        query = query_latest_model
        data_set = (identifier,)

    else:
        query = query_given_model
        data_set = (identifier, name)

    db_cursor = conn.cursor()
    db_cursor.execute(query, data_set)

    result = db_cursor.fetchone()

    conn.commit()
    db_cursor.close()

    return result


def change_active_model(model_tag, model_name=None):
    """
    Find the active model and change its state to false. Then find the given model an activate it
    :param model_name: model name to be activated
    :return: Current recommender is changed with the given one.
    """
    conn = create_database_connection(db_path)

    # De-activate currently active model
    db_cursor = conn.cursor()
    db_cursor.execute(query_deactivate_model)

    if model_name is None:
        # Get all models with the given tag
        query_get_models = """ SELECT id FROM ecommerce_recommender_model WHERE identifier = """ + '\'' +  str(model_tag) + '\''
        db_cursor = conn.cursor()
        db_cursor.execute(query_get_models)
        # Get the newest model
        newest_model_id = db_cursor.fetchall()
        newest_model_id = newest_model_id[-1:][0][0]

        query_activate_model = """ UPDATE ecommerce_recommender_model SET active = """  '\'' + 'TRUE' + '\'' " WHERE id = """ + '\'' +  str(newest_model_id) + '\''
        db_cursor = conn.cursor()
        db_cursor.execute(query_activate_model)

    else:
        query_activate_model = " UPDATE ecommerce_recommender_model SET active = " '\'' + "TRUE" + '\'' " WHERE name = " + '\'' + model_name + '\''
        db_cursor = conn.cursor()
        db_cursor.execute(query_activate_model)
        pass

    conn.commit()
    db_cursor.close()
    return db_cursor.lastrowid


def delete_old_models():
    """
    Deletes the saved models older than 30 days.
    """
    conn = create_database_connection(db_path)

    import datetime
    curr_time = datetime.datetime.now() - datetime.timedelta(days=30)

    query_delete_old_models = "DELETE FROM ecommerce_recommender_model WHERE created < " + '\'' + str(curr_time) + '\''
    db_cursor = conn.cursor()
    db_cursor.execute(query_delete_old_models)

    conn.commit()
    db_cursor.close()
    return db_cursor.lastrowid


def create_database_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn


def add_new_item(conn, _object_id, _attribute, _value):
    """
    Add a new item with given id, attribute and value
    :param conn: Db connection object
    :param _object_id: Item id
    :param _attribute: Item attribute
    :param _value: Attribute value
    :return:
    """

    sql_new_item = query_insert_item
    db_cursor = conn.cursor()

    # If there is no item with same ID AND Attribute
    query = " SELECT object_id FROM ecommerce_item WHERE object_id = " + str(_object_id) + " AND attribute = " + '\'' + _attribute + '\''
    db_cursor.execute(query)
    result = db_cursor.fetchone()

    if result is None:
        data_set = (_object_id, _attribute, _value)
        db_cursor.execute(sql_new_item, data_set)
        conn.commit()

    db_cursor.close()
    return db_cursor.lastrowid


def delete_item(conn, _object_id):
    """
    :param conn: db connection object
    :param _object_id: ID of the object to be deleted
    :return: Item is deleted with is all features
    """
    sql_delete_item = query_delete_item

    db_cursor = conn.cursor()
    db_cursor.execute(sql_delete_item, (_object_id,))
    conn.commit()

    db_cursor.close()
    return db_cursor.lastrowid


def update_item(conn, _object_id, _attribute, _value):
    """
    :param conn: db connection object
    :param _object_id: ID of the object to be deleted
    :param _attribute: Attribute to be updated (must exist)
    :param _value: New value for the attribute
    :return: Item attribute is updated.
    """
    sql_update_item = query_update_item

    data_set = (_value, _object_id, _attribute)

    db_cursor = conn.cursor()
    db_cursor.execute(sql_update_item, data_set)
    conn.commit()

    db_cursor.close()
    return db_cursor.lastrowid


def add_new_user(_user_id, item_id):
    """
    :param _user_id: Current user Id
    :param item_id: Current item user clicked on
    :return: New user add. If the user is already there, new row added with the item user clicked on
    """
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()

    # If user is not present in the table, add it
    query_user = query_check_user
    db_cursor.execute(query_user)
    result = db_cursor.fetchone()

    # TODO: I believe checking user is not necessary since we will always need to append item to user id
    if result is None:
        # Insert user
        query_insert = query_add_user
        data_set = (_user_id, item_id)
        db_cursor.execute(query_insert, data_set)
        conn.commit()

    db_cursor.close()
    return db_cursor.lastrowid


def find_object_id(_object_id):
    """
    Finds the given item in the database
    :param _object_id: Item ID
    :return: 1 if item is found. Otherwise 0
    """
    conn = create_database_connection(db_path)

    query = query_check_item

    data_set = (_object_id,)

    db_cursor = conn.cursor()
    db_cursor.execute(query, data_set)

    result = db_cursor.fetchone()
    conn.commit()

    db_cursor.close()

    # Return 0 if item does not exist, otherwise return 1
    if result is None:
        return 0
    else:
        return 1

def find_popular_items(filter_date=365):
    import datetime
    from ecommerce.utils.helper_scripts.pre_process import popular_item_list_generator
    conn = create_database_connection(db_path)
    # Example date format to query: '23/06/2018 00:00';
    start_date = datetime.datetime.now() - datetime.timedelta(days=filter_date)
    start_date = start_date.strftime("%Y/%m/%d %H:%M")
    sql_date_swap = """ substr(last_modified,7,4) || '/' || substr(last_modified,4,2) || '/' || substr(last_modified,1,2) || ' ' || substr(last_modified,12) """

    query = """ select * from ecommerce_user where """ + sql_date_swap + """  > ? ORDER BY """ + sql_date_swap + """ DESC;"""

    data_set = (start_date,)

    db_cursor = conn.cursor()
    db_cursor.execute(query, data_set)
    user_data = db_cursor.fetchall()

    pop_item_list = popular_item_list_generator(user_data)

    # Convert list to string and save it to db
    listToStr = ', '.join(map(str, pop_item_list))

    query = """ INSERT INTO ecommerce_popular_items ('pop_item_id') VALUES(?);"""
    data_set = (listToStr,)

    db_cursor = conn.cursor()
    db_cursor.execute(query, data_set)
    conn.commit()

    db_cursor.close()

def retrieve_popular_items(filter_date=365):
    conn = create_database_connection(db_path)

    query = """ SELECT pop_item_id FROM ecommerce_popular_items;"""

    db_cursor = conn.cursor()
    db_cursor.execute(query)
    popular_items = db_cursor.fetchall()

    # Get the latest popular items
    popular_items = popular_items[-1:]

    conn.commit()
    db_cursor.close()

    # Cursor will return a tuple which contains PK and varchar (that has item ids separeted by comma)
    # Get the varchar, iterate over it and remove commas.
    popular_items = popular_items[0][0].split()

    for i in range(len(popular_items)):
        popular_items[i] = popular_items[i].replace(',', '')

    return popular_items

def insert_recommendation_performance(user_id, item_count, rec_perf, precision_perf, mrr_perf, model):
    """
    save evaluation results of the given recommender model to database.
        example db row: <user_id> <precision> <recall> <mrr> <recommendation_model>
    :param user_id: User ID
    :param item_count: Item count in the user sequnce
    :param rec_perf: Recall Result
    :param precision_perf: Precision Result
    :param mrr_perf: MRR Result
    :param model: Model Tag
    :return: Save the performance to db
    """
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()
    data_set = (user_id, item_count, rec_perf, precision_perf, mrr_perf, model)
    db_cursor.execute(query_insert_recommendation_performance, data_set)
    conn.commit()

    db_cursor.close()

def get_user_data():
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()
    db_cursor.execute("""Select * FROM ecommerce_user;""")
    user_data = db_cursor.fetchall()

    return user_data


def create_user_sequences():
    """
    Method iterates through every row in the ecommerce_user table. Find same users and items that are clicked by
    the user. Merges all items in one list to create a sequence.
        -> pk   user_id      user_sequence
        -> 1	531244	    4805,3,2155,4728
    :return: User sequences are created and saved in DB (Takes 6 hours to finish..)
    """
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()
    db_cursor.execute(query_user_ids)
    user_ids = db_cursor.fetchall()

    user_sequences_dict = {}

    for user in range(len(user_ids)):
        data_set = (user_ids[user][0],)
        db_cursor.execute(query_user_items, data_set)
        item_list = db_cursor.fetchall()
        str_seq = ''

        # Consider sequences only longer than 2 items
        if len(item_list) > 2:
            user_sequence = []
            for item in range(len(item_list)):
                user_sequence.append(item_list[item][0])
                str_seq += str(item_list[item][0]) + ','

            data_set = (user_ids[user][0], str_seq)
            db_cursor.execute(query_insert_user_sequence, data_set)
            conn.commit()

            user_sequences_dict[user_ids[user][0]] = user_sequence

    conn.commit()
    db_cursor.close()
    return user_sequences_dict


def get_all_user_sequences():
    """
    To train item2vec.
    We need every single item to be tokenized string in a list.
    Method retrieves all sequences which have more than 2 items in it. Then splits the string of items to create list
    :return: list. items = [ user_id, ['id1', 'id2', 'id3'] ]
    """
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()
    db_cursor.execute(query_all_sequence,)
    item_list = db_cursor.fetchall()

    items = []
    counter = 0
    for item in item_list:
        string_id_list = item[1].split(',')
        del string_id_list[-1] # Last element will be always ','
        temp = []
        for i_id in string_id_list:
            temp.append((i_id))
        items.append([item[0], temp])

    return items


def retrieve_user_sequences(item_id):
    """
    Get all user sequences and find the ones with current item id in it.
    Method not only finds user sequences from the database but also trims the user sequences based on the given item id.
    As an example:
        Imagine we have following user sequence: [1881, 25, 1923, 97, 1938]
        And user clicked on item '1923'. That means next item will be '97'.
        So I am trimming the sequence after item '1923'. Then new sequence will look like: [97, 1938]
        Then I can see compare my recommendations with this new sequence.
    :param item_id: Item id user clicked on
    :return: user_sequences_dict
    """
    conn = create_database_connection(db_path)
    db_cursor = conn.cursor()

    item_id_sql_like = ('%,' + str(item_id) + ',%', )
    db_cursor.execute(query_find_sequence_like, item_id_sql_like)
    item_list = db_cursor.fetchall()

    conn.commit()
    db_cursor.close()

    user_sequences_dict = {}

    # Turn string list to int
    items = []
    for item in item_list:
        string_id_list = item[1].split(',')
        del string_id_list[-1] # Last element will be always ','
        temp = []
        for i_id in string_id_list:
            temp.append(int(i_id))
        items.append([item[0], temp])

    # Iterate through the items in each list end delete the items before our current item.
    counter = 0
    for ids in items:
        item_index = ids[1].index(int(item_id))
        if item_index is not 0:
            items[counter][1] = ids[1][item_index + 1:]
        counter += 1

    # Find item sequences longer than 1 item
    for seq in items:
        if len(seq[1]) > 2:
            user_sequences_dict[seq[0]] = seq[1]

    return user_sequences_dict


def daily_updates(update_dict):
    """
        Structure for daily updates :
            {
            'new_item':
                      { 'attribute_1' : 'value_1',
                        'attribute_2' : 'value_2', },
            'update_item':
                      { 'attribute_1' : 'value_1',
                        'attribute_2' : 'value_2', },
            'delete_item':
                      [ 'item_1_id', 'item_2_id' ]
            }
    """
    conn = create_database_connection(db_path)

    for item_operation, item_dictionary in update_dict.items():
        if item_operation == 'new_item':
            for item_id, item_data in item_dictionary.items():
                for attribute, value in item_data.items():
                    add_new_item(conn, item_id, attribute, value)

        elif item_operation == 'delete_item':
            for item_id in item_dictionary:
                delete_item(conn, item_id)

        elif item_operation == 'update_item':
            for item_id, item_data in item_dictionary.items():
                for attribute, value in item_data.items():
                    update_item(conn, item_id, attribute, value)

        # TODO: add item_operation == 'add_user'

    conn.close()
