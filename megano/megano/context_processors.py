from store.models import Category


def get_static_template_category(request):
    return {'static_template_category': Category.objects.all()}
