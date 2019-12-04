from django.db import models
from django.shortcuts import reverse
from django_celery_results.models import TaskResult

from ecommerce.utils.recommendation_scripts.Doc2VecHelper import doc2vec_calculate_similarity
from ecommerce.utils.recommendation_scripts.Item2VecHelper import item2vec_calculate_similarity
from ecommerce.utils.recommendation_scripts.RnnHelper import rnn_calculate_similarity

from ecommerce.utils.helper_scripts.Utils import create_recommendations


# Create your models here.
class Item(models.Model):
    """
        Item class that is represent an item in the database.
        To make the application as generic as possible, triplestore(??) method is used, so we can add as much as
        items with different amount of attributes and their corresponding values.
    """
    object_id = models.IntegerField(null=False, unique=False)
    attribute = models.TextField(max_length=75, unique=False, null=False)
    value = models.TextField(max_length=3000, unique=False, blank=True)

    def __str__(self):
        return self.attribute

    def get_value(self):
        return self.value

    def get_absolute_url(self):
        # Creates an URL with the item primary key appended at the end. So we can navigate to dedicated item page.
        return reverse("ecommerce:item", kwargs={'pk': self.object_id})

    def return_home(self):
        return reverse("ecommerce:home")

    @property
    def recommendation_algorithm(self):
        return self.recommendation_algorithm

    @recommendation_algorithm.setter
    def recommendation_algorithm(self, name):
        self.recommendation_algorithm = name

    def recommend_item(self):
        """
        There are currently 3 implementations of getting a recommendation.
            1. Item2Vec = 'i2v'
            2. Doc2Vec = 'd2v'
            3. Recurrent Neural Network (Sequence Prediction) = 'rnn'

        :return: Method will update the current recommendation method and return corresponding recommendations
        """
        from ecommerce.utils.helper_scripts.DatabaseOperations import change_active_model

        change_active_model(model_tag=self.recommendation_algorithm)

        if self.recommendation_algorithm == 'i2v':
            return self.item2vec_recommend()

        elif self.recommendation_algorithm == 'd2v':
            return self.doc2vec_recommend()

        elif self.recommendation_algorithm == 'rnn':
            return self.rnn_recommend()

    def doc2vec_recommend(self):
        similar_items = doc2vec_calculate_similarity(self.object_id)
        items_dict = create_recommendations(similar_items)

        return [items_dict]

    def item2vec_recommend(self):
        similar_items = item2vec_calculate_similarity(self.object_id)
        items_dict = create_recommendations(similar_items)

        return [items_dict]

    def rnn_recommend(self):
        similar_items = rnn_calculate_similarity(self.object_id)
        items_dict = create_recommendations(similar_items)

        return [items_dict]


class User(models.Model):
    user_id = models.IntegerField(null=False, unique=False)
    object_id = models.IntegerField(unique=False, null=False)
    last_modified = models.DateField(unique=False, blank=True)

    def __str__(self):
        return self.user_id + ' ' + self.object_id
