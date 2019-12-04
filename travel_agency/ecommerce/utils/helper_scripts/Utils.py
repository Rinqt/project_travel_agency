from django.apps import apps


def create_recommendations(similar_items):
    """
        Gets the dictionary for similar items and extracts the necessary information for the front-end

    :param similar_items: Item dictionary
    :return: items_dict that holds specific attributes and their value
    """
    Item = apps.get_model('ecommerce', 'Item')

    items_dict = {}

    for key, rec in enumerate(similar_items[1:4]):
        items_dict[key] = {}
        obj = Item.objects.values('attribute', 'value').filter(object_id=rec)
        for dict_attribute in obj:
            if dict_attribute['attribute'] == 'nazev':
                items_dict[key][dict_attribute['attribute']] = dict_attribute['value']

            elif dict_attribute['attribute'] == 'nazev_typ':
                items_dict[key][dict_attribute['attribute']] = dict_attribute['value']

            elif dict_attribute['attribute'] == 'zeme':
                items_dict[key][dict_attribute['attribute']] = dict_attribute['value']

            elif dict_attribute['attribute'] == 'prumerna_cena':
                items_dict[key][dict_attribute['attribute']] = dict_attribute['value']

            elif dict_attribute['attribute'] == 'delka':
                items_dict[key][dict_attribute['attribute']] = dict_attribute['value']

        items_dict[key]['url'] = '/item/' + str(rec)

    return items_dict


def create_item_dict(context, create_item_detail=False):
    """
           Creates a dictionary that contains information of a specific item or items if user is in the homepage.
           Then return it to front-end.

    :param context: Context of the current web page
    :param create_item_detail: If true, create a dictionary for an individual item to use in Item DetailView.
                               If false, create a dictionary that contains 6 items for each page on the homepage.
    :return: Item(s) dictionary that holds items id, attributes with their values.
    """
    Item = apps.get_model('ecommerce', 'Item')

    if create_item_detail:
        # Find the item that user clicked in database, loop through its attributes-values and concatenate them
        # with '#' symbol. So, then we can process the dictionary to find what is the attribute name and its
        # value to use in front-end.
        all_destination = context['item']
        individual_item = Item.objects.filter(object_id=all_destination.object_id)

        item_dict = {context['item'].object_id: concat_item_attributes(individual_item)}

        return dict(process_dictionary(item_dict))

    else:
        # Since we are in the homepage now, we get the context of the page which has 'paginate_by' number of items.
        # Loop through its attributes-values and concatenate them with '#' symbol. So, then we can process the
        # dictionary to find what is the attribute name and its value to use in front-end.
        all_destination = context['item_list']

        item_dict = {}
        for destination in all_destination:
            individual_item = Item.objects.filter(object_id=destination.object_id)
            item_dict[destination.object_id] = concat_item_attributes(individual_item)

        # Process the item dictionary
        return dict(process_dictionary(item_dict))


def process_dictionary(item_dictionary):
    """ Receives the dictionary and transformers it in a way to be used in front-end.

    :param item_dictionary: dictionary that holds item(s) data which is concatenated by '#' symbol.
                            { 'item_id': { 'att1#att2#att3':'val1#val2#val3# } }

    :return: dictionary that holds item information with better structure so it can be processed on front-end easily.
                            { 'item_id': { 'att1':'val1'
                                           'att2':'val1'
                                           'att3':'val3' } }
    """
    for key, value in item_dictionary.items():
        # Create an item object and split the attributes
        item = item_dictionary[key]
        item_attributes = item['attribute'].split('#')
        item_values = item['value'].split('#')

        # Delete last elements of the lists since it will always be empty. Because of the last # symbol
        del item_attributes[-1]
        del item_values[-1]

        # Iterate through the attribute and value lists together and create the final dictionary with the structure
        # that is described on "return" section of the method comment.
        for item_attribute, item_value in zip(item_attributes, item_values):
            if not item_value:
                item_value = 'Ask for information'
            item_dictionary[key][item_attribute] = item_value

    return item_dictionary


def get_popular_items():
    """
    TODO: write
    :param last_n_days:
    :return:
    """
    from ecommerce.utils.helper_scripts.DatabaseOperations import retrieve_popular_items
    
    item_list = retrieve_popular_items()

    Item = apps.get_model('ecommerce', 'Item')

    item_dict = {}

    for item_id in item_list:
        individual_item = Item.objects.filter(object_id=item_id)
        item_dict[item_id] = concat_item_attributes(individual_item)

    return dict(process_dictionary(item_dict))


def concat_item_attributes(individual_item):
    temp = dict(id=None, attribute='', value='')

    for data in individual_item:
        # Start building up the item
        temp['id'] = data.object_id
        temp['attribute'] += data.attribute + '#'
        temp['value'] += data.value + '#'

    return temp
