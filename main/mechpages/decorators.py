from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.urlresolvers import reverse_lazy


def verified_mobile_required(function=None, login_url=reverse_lazy('ajax_verify_pin'),
                             redirect_field_name=REDIRECT_FIELD_NAME):
    actual_decorator = user_passes_test(
        lambda u: u.userprofile.mobile_verified,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def is_mechanic_check(function=None, login_url=reverse_lazy('not_allowed'), redirect_field_name=None):
    actual_decorator = user_passes_test(
        lambda u: u.userprofile.is_mechanic,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def is_mechanic_required(view_func):
    decorated_view_func = login_required(is_mechanic_check(verified_mobile_required(view_func)))
    return decorated_view_func


def is_mechanic_profile_complete_check(function=None, login_url=reverse_lazy('profile_required'),
                                       redirect_field_name=None):
    actual_decorator = user_passes_test(
        lambda u: u.userprofile.profile_complete,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def profile_complete_required(view_func):
    decorated_view_func = login_required(
        is_mechanic_check(verified_mobile_required(is_mechanic_profile_complete_check(view_func))))
    return decorated_view_func


def is_user_check(function=None, login_url=reverse_lazy('not_allowed'), redirect_field_name=None):
    actual_decorator = user_passes_test(
        lambda u: not u.userprofile.is_mechanic,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def is_user_required(view_func):
    decorated_view_func = login_required(is_user_check(view_func))
    return decorated_view_func
