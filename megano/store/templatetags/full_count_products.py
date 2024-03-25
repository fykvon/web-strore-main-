from django import template


register = template.Library()


@register.filter(name="count")
def total_number(args, offers: list):
    amount = [count.amount for count in offers]
    summ = sum(amount)
    return summ
