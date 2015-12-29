from django import template
from mechpages.util import check_send_rate

register = template.Library()


@register.filter(name='check_send_rate_tag')
def check_send_rate_tag(request):
    return check_send_rate(request, False)
