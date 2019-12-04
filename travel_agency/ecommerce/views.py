from .models import Item
from django.views.generic import ListView, DetailView
from ecommerce.utils.helper_scripts.Utils import create_item_dict, get_popular_items


class HomeView(ListView):
    """
        List view for homepage.
        Home page is paginated by 6 items and items are ordered based on their id.
        Default recommendation algorithm is set to Item2Vec (i2v)
        # TODO: We can change the recommendation algorithm based on user id.
        # TODO: Might be better to order items by the date which they are added to DB
    """
    model = Item
    paginate_by = 6
    template_name = "home.html"
    ordering = ['id']
    Item.recommendation_algorithm = 'i2v'

    def get_context_data(self, **kwargs):
        # Get the context of the page and create a dictionary which will have information for the items on the homepage.
        context = super().get_context_data(**kwargs)
        context['destination_dictionary'] = create_item_dict(context, False)
        context['popular_destinations'] = get_popular_items()
        return context


class ItemDetailView(DetailView):
    """
        Detail view for an individual item.
    """
    model = Item
    template_name = "item.html"

    def get_context_data(self, **kwargs):
        # Get the context of the page and create an item dictionary for a specific item that user is currently visiting.
        context = super().get_context_data(**kwargs)
        context['destination_dictionary'] = create_item_dict(context, True)

        return context
