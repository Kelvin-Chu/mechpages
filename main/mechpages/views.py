import traceback
from allauth.account.decorators import verified_email_required
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.utils.timezone import localtime
from postman.templatetags.postman_tags import compact_date
import simplejson
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from postman.views import FolderMixin, WriteView, ReplyView
from allauth.account.utils import get_next_redirect_url
from allauth.account.views import SignupView, PasswordChangeView, PasswordSetView, EmailView, PasswordResetFromKeyView
from allauth.utils import get_request_param, get_user_model
from django.apps import apps
from twilio.rest import TwilioRestClient
from main import settings
from builtins import property, super, int, Exception, str, float, reversed, list, object, len
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import UpdateView, CreateView, ListView, TemplateView
from .forms import UpdateUserProfileForm, VerifyPinForm, ProfileWizardForm1, ProfileWizardForm3, \
    ProfileWizardForm2JobHistory, ProfileWizardForm2Skills, ProfileWizardForm4, ProfileWizardForm5, \
    UpdateMechanicProfileForm, FullReplyFormOverride, WriteFormOverride, AnonymousWriteFormOverride, ReviewForm, \
    PostAJobForm, ContactForm, AvatarUploadForm
from .forms_override import CustomAddEmailForm, CustomChangePasswordForm, CustomSetPasswordForm, \
    CustomResetPasswordKeyForm
from .util import trim_mobile, check_send_attempts, get_pin, check_verify_attempts, verify_pin, check_mobile, \
    get_mechanics_list, get_mechanics_profile, get_mechanics_nearest, check_email, check_send_rate, get_name_icon, \
    get_requests_list, get_requests_nearest, get_request, get_icon_url_from_user, get_thumbnail_url_from_user
from .models import UserProfile, MobileNumber, Location, SkillChoice, NotifyAvailability, Review, PostAJob
from .decorators import is_user_required, is_mechanic_required, verified_mobile_required, profile_complete_required


def initial_home(request):
    if request.user.is_authenticated():
        return redirect(reverse_lazy('browse'))
    else:
        return redirect(reverse_lazy('home'))


# Setting tiny to an empty string so the nav bar will not start at the top of the page
# Note: there is also a small javascript in index.html that goes with this feature
def home(request):
    # return render(request, "index.html", {'tiny': ' '})
    return render(request, "index.html", {})


def not_allowed(request):
    return render(request, "403.html", {})


def terms_of_use(request):
    return render(request, "terms_of_use.html", {})


def privacy_policy(request):
    return render(request, "privacy_policy.html", {})


def contact(request):
    form_class = ContactForm

    if request.method == 'POST':
        form = form_class(data=request.POST)
        if form.is_valid():
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            message = request.POST.get('message', '')
            template = get_template('contact_template.txt')
            context = Context({
                'name': name,
                'email': email,
                'message': message,
            })
            content = template.render(context)
            email = EmailMessage(
                "New contact form submission",
                content,
                "no-reply@mechpages.com",
                ['admin@mechpages.com'],
                headers={'Reply-To': email}
            )
            email.send()
            return redirect('contact_success')
    return render(request, 'contact.html', {'form': form_class, })


def contact_success(request):
    return render(request, "contact_success.html", {})


@is_mechanic_required
def profile_required(request):
    return render(request, "mechanics/profile_required.html", {})


@is_mechanic_required
def tools(request):
    return render(request, "mechanics/tools.html", {})


class MechanicSignupView(SignupView):
    template_name = "mechanics/signup_mechanic.html"


mechanic_signup = MechanicSignupView.as_view()


# Overriding default allauth email form to limit the number of characters allowed in the field
class CustomEmailView(EmailView):
    form_class = CustomAddEmailForm


custom_email = login_required(CustomEmailView.as_view())


# Overriding default allauth password form to limit the number of characters allowed in the field
class LoginAfterPasswordChangeView(PasswordChangeView):
    form_class = CustomChangePasswordForm

    @property
    def success_url(self):
        return reverse_lazy('account_login')


login_after_password_change = login_required(LoginAfterPasswordChangeView.as_view())


# Overriding default allauth password form to limit the number of characters allowed in the field
class LoginAfterPasswordSetView(PasswordSetView):
    form_class = CustomSetPasswordForm

    @property
    def success_url(self):
        return reverse_lazy('account_login')


login_after_password_set = login_required(LoginAfterPasswordSetView.as_view())


# Overriding default allauth password form to limit the number of characters allowed in the field
class LoginAfterPasswordResetFromKeyView(PasswordResetFromKeyView):
    form_class = CustomResetPasswordKeyForm

    @property
    def success_url(self):
        return reverse_lazy('account_login')


password_reset_from_key = LoginAfterPasswordResetFromKeyView.as_view()


class UpdateUserProfileView(UpdateView):
    form_class = UpdateUserProfileForm
    template_name = 'account/profile_user.html'
    success_url = reverse_lazy('profile_user', kwargs={'success': 'success'})

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super(UpdateUserProfileView, self).get_context_data(**kwargs)
        if 'success' in self.kwargs:
            context['success'] = self.kwargs['success']
        return context


update_profile_user = is_user_required(UpdateUserProfileView.as_view())


class UpdateMechanicProfileView(UpdateView):
    form_class = UpdateMechanicProfileForm
    template_name = 'mechanics/profile_mechanic.html'
    success_url = reverse_lazy('profile_mechanic', kwargs={'success': 'success'})

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super(UpdateMechanicProfileView, self).get_context_data(**kwargs)
        if 'success' in self.kwargs:
            context['success'] = self.kwargs['success']
        return context


update_profile_mechanic = is_mechanic_required(UpdateMechanicProfileView.as_view())


@login_required
def ajax_send_pin(request):
    # Sends SMS PIN to the specified number
    try:
        mobile_number = trim_mobile(request.POST.get('id_mobile', ""))
        check_attempts_resp = check_send_attempts(request.user)
        if check_attempts_resp is not None:
            return check_attempts_resp
        check_mobile_resp = check_mobile(request.user, mobile_number)
        if check_mobile_resp is not None:
            return check_mobile_resp
        pin = get_pin()
        # store the PIN in the cache for later verification.
        cache.set(mobile_number + "_pin", pin, 1 * 3600)  # valid for 1 hr
        client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    except Exception:
        # print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=403)
    try:
        client.messages.create(
            body="Howdy From MechPages! Please enter %s in the PIN section to validate your mobile number." % pin,
            to=mobile_number, from_=settings.TWILIO_FROM_NUMBER)
        count = cache.incr(str(request.user) + "_sendpin")
        if count > 6:
            cache.set(str(request.user) + "_sendpin_timeout", 1, 3600)
        elif count > 3:
            cache.set(str(request.user) + "_sendpin_timeout", 1, 30)
    except Exception:
        return HttpResponse("Not sent! Check your mobile number.", status=403)
    return HttpResponse("")


class AjaxVerifyPinView(CreateView):
    model = MobileNumber
    form_class = VerifyPinForm
    template_name = 'verify_mobile.html'
    redirect_field_name = 'next'

    # CreateView has no object to edit so it needs to be set to None, otherwise it will throw no attribute object error
    # http://stackoverflow.com/questions/23774412/attributeerror-myview-has-no-attribute-object-in-custom-mixin-in-django
    def __init__(self, **kwargs):
        super(AjaxVerifyPinView, self).__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        next_url = get_next_redirect_url(self.request, self.redirect_field_name)
        if next_url:
            return "%s" % next_url
        elif self.request.user.userprofile.is_mechanic:
            return reverse_lazy('profile_mechanic', kwargs={'success': 'success'})
        else:
            return reverse_lazy('profile_user', kwargs={'success': 'success'})

    # hack where if 'mechanic' is in the url, it will activate a hidden input in the template to convert the user
    # to a mechanic.  if the user is already a mechanic, redirect to browse.  if the user is already mobile_verified,
    # redirect to mechanic_convert.  if mechanic is not in the url, serve verify_mobile normally.
    def get(self, request, *args, **kwargs):
        if 'mechanic' in self.kwargs:
            if request.user.userprofile.is_mechanic:
                return redirect(reverse_lazy('browse'))
            if request.user.userprofile.mobile_verified:
                return redirect(reverse_lazy('mechanic_convert'))
            return super(AjaxVerifyPinView, self).get(request, *args, **kwargs)
        else:
            return super(AjaxVerifyPinView, self).get(request, *args, **kwargs)

    # normally I would handle data verification and modification via django form but it's easier to handle error
    # response for ajax in the view (http://alexkehayias.tumblr.com/post/14020155360/django-form-validation-ajax)
    def post(self, request, **kwargs):
        mobile_number = trim_mobile(request.POST.get('id_mobile', ""))
        pin = request.POST.get('id_pin', "")
        check_attempts_resp = check_verify_attempts(request.user)
        if check_attempts_resp is not None:
            return check_attempts_resp
        check_mobile_resp = check_mobile(request.user, mobile_number)
        if check_mobile_resp is not None:
            return check_mobile_resp
        if pin.isdigit():
            if verify_pin(request.user, mobile_number, int(pin)):
                profile = request.user.userprofile
                profile.mobile = mobile_number
                if not MobileNumber.objects.filter(mobile=mobile_number).exists() and not profile.mobile_verified:
                    MobileNumber.objects.create(mobile=mobile_number)
                    profile.review_points += 5
                profile.mobile_verified = True
                # hack that checks a hidden input from the form from mechanic signup pages
                if request.POST.get('id_is_mechanic', False):
                    profile.is_mechanic = True
                    profile.skills.add(11)
                profile.save()
                cache.delete(mobile_number)
                cache.delete(str(request.user) + "_verifypin")
                cache.delete(str(request.user) + "_verifypin_timeout")
                return HttpResponse(self.get_success_url())
            else:
                return HttpResponse("Incorrect PIN", status=404)
        else:
            return HttpResponse("Incorrect PIN", status=404)

    def get_context_data(self, **kwargs):
        context = super(AjaxVerifyPinView, self).get_context_data(**kwargs)
        redirect_field_value = get_request_param(self.request, self.redirect_field_name)
        if 'mechanic' in self.kwargs:
            context['mechanic'] = self.kwargs['mechanic']
        context.update({"redirect_field_name": self.redirect_field_name, "redirect_field_value": redirect_field_value})
        return context


ajax_verify_pin = login_required(AjaxVerifyPinView.as_view())


@is_user_required
@verified_mobile_required
def mconvert(request):
    if request.method == 'GET':
        return render(request, "account/mconvert.html", {})
    if request.method == 'POST':
        request.user.userprofile.is_mechanic = True
        request.user.userprofile.skills.add(11)
        request.user.userprofile.save()
        return redirect(reverse_lazy('profile_wizard'))


@is_mechanic_required
def delete(request):
    pk = request.POST.get('item_pk')
    page = request.POST.get('page')
    model = request.POST.get('model')
    if request.method == 'POST' and pk and model in ('ProjectImage', 'JobHistory'):
        try:
            item = apps.get_model('mechpages', model).objects.get(pk=pk)
            if request.user == item.user:
                item.delete()
                return HttpResponseRedirect(reverse_lazy('profile_wizard') + "?page=%s" % page)
            else:
                return HttpResponseRedirect(reverse_lazy('not_allowed'))
        except Exception:
            return HttpResponseRedirect(reverse_lazy('not_allowed'))
    return HttpResponseRedirect(reverse_lazy('not_allowed'))


@is_mechanic_required
def remove_skill(request):
    pk = request.POST.get('item_pk')
    if request.method == 'POST' and pk:
        try:
            request.user.userprofile.skills.remove(pk)
            return HttpResponseRedirect(reverse_lazy('profile_wizard') + "?page=2")
        except Exception:
            return HttpResponseRedirect(reverse_lazy('not_allowed'))
    return HttpResponseRedirect(reverse_lazy('not_allowed'))


@is_mechanic_required
def add_skills(request):
    if request.method == 'POST':
        form = ProfileWizardForm2Skills(request.POST)
        if form.is_valid():
            request.user.userprofile.skills = form.cleaned_data['skills']
            request.user.userprofile.save()
    return HttpResponseRedirect(reverse_lazy('profile_wizard') + "?page=2")


class ProfileWizardView(UpdateView):
    page_field_name = 'page'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = super(ProfileWizardView, self).get_context_data(**kwargs)
        page = get_request_param(self.request, self.page_field_name, default='1')
        # there are 2 forms in page2, one for job history and one for skills.  the job history is the default
        # and the 2nd form has to be added and initialized separately
        if page == '2':
            context['form2'] = ProfileWizardForm2Skills(**self.get_form_kwargs())
        return context

    def get_form_class(self):
        page = get_request_param(self.request, self.page_field_name, default='1')
        forms = {'1': ProfileWizardForm1, '2': ProfileWizardForm2JobHistory, '3': ProfileWizardForm3,
                 '4': ProfileWizardForm4, '5': ProfileWizardForm5}
        for i in ('1', '2', '3', '4', '5'):
            if page == i:
                return forms[i]
        return ProfileWizardForm1

    def get_template_names(self):
        page = get_request_param(self.request, self.page_field_name, default='1')
        for i in ('1', '2', '3', '4', '5'):
            if page == i:
                return "mechanics/profile_wizard_%s.html" % i
        return '403.html'

    # each page has 3 possible success url based off of the name of the submit input in the template:
    #   1) Save form and go to previous url
    #   2) Save form and go to next url
    #   3) Save form and stay in the same page
    def get_success_url(self):
        for i in ('1', '2', '3', '4', '5'):
            if ('page%snext' % i) in self.request.POST:
                if int(i) < 5:
                    return reverse_lazy('profile_wizard') + "?page=%s" % str(int(i) + 1)
                if int(i) == 5:
                    return reverse_lazy('tools')
            elif ('page%sprev' % i) in self.request.POST:
                if int(i) > 1:
                    return reverse_lazy('profile_wizard') + "?page=%s" % str(int(i) - 1)
            elif ('page%s' % i) in self.request.POST:
                return reverse_lazy('profile_wizard') + "?page=%s" % str(int(i))
        return reverse_lazy('not_allowed')

    # If 'page2' is in the POST instead of 'page2prev' or 'page2next', then it means the user clicked the 'Add another'
    # button from the template.  Clicking the 'Add another' button require the form the be filled while 'page2prev'
    # or 'page2next' does not.
    def get_form_kwargs(self):
        kwargs = super(ProfileWizardView, self).get_form_kwargs()
        if self.get_form_class() is ProfileWizardForm2JobHistory:
            if 'page2' in self.request.POST:
                kwargs.update({'required': True})
        return kwargs


profile_wizard = is_mechanic_required(ProfileWizardView.as_view())


class BrowseView(ListView):
    template_name = 'browse.html'
    model = Location

    def get_context_data(self, **kwargs):
        context = super(BrowseView, self).get_context_data(**kwargs)
        query = get_request_param(self.request, 'query', default='')
        mech_id = get_request_param(self.request, 'mech_id', default='')
        skill = get_request_param(self.request, 'skill', default='')
        context['query'] = query
        context['mech_id'] = mech_id
        context['skill'] = skill
        context['skillChoice'] = SkillChoice.objects.all()
        return context


browse = BrowseView.as_view()


def ajax_get_mechanics(request):
    try:
        sw_lat = float(request.POST.get('id_sw_lat').strip(' "'))
        sw_lng = float(request.POST.get('id_sw_lng').strip(' "'))
        ne_lat = float(request.POST.get('id_ne_lat').strip(' "'))
        ne_lng = float(request.POST.get('id_ne_lng').strip(' "'))
        skill = request.POST.get('id_skill')
        mechanics_list = get_mechanics_list(sw_lat, sw_lng, ne_lat, ne_lng, skill)
        result = [{"pk": x[0], "latlng": (x[1], x[2]), "radius": x[3],
                   "icon": get_icon_url_from_user(get_user_model().objects.get(pk=x[4]))} for x in mechanics_list]
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


def ajax_get_mechanic_profile(request):
    try:
        x = get_mechanics_profile(int(request.POST.get('id_pk')))
        result = {"id": x[0], "thumbnail": x[1], "name": x[2], "skills": x[3], "bio": x[4], "jobhistory": x[5],
                  "images": x[6], "captcha": check_send_rate(request), "rating": x[7], "ratingcount": x[8]}
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


def ajax_get_mechanics_nearest(request):
    try:
        lat = float(request.POST.get('id_lat').strip(' "'))
        lng = float(request.POST.get('id_lng').strip(' "'))
        skill = request.POST.get('id_skill')
        mechanics_nearest = get_mechanics_nearest(lat, lng, skill)
        result = [{"pk": x[0], "name": x[1], "miles": x[2], "bio": x[3], "icon": x[4], "skills": x[5], "rating": x[6],
                   "ratingcount": x[7]} for x in mechanics_nearest]
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


def ajax_subscribe_availability(request):
    try:
        email = request.POST.get('id_email', "")
        lat = float(request.POST.get('id_lat').strip(' "'))
        lng = float(request.POST.get('id_lng').strip(' "'))
        check = check_email(email)
        if check is not None:
            return check
        subscriber = NotifyAvailability(email=email, latitude=lat, longitude=lng)
        subscriber.save()
        return HttpResponse("")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


def ajax_send_message(request):
    form_classes = (WriteFormOverride, AnonymousWriteFormOverride)
    form_class = form_classes[0] if request.user.is_authenticated() else form_classes[1]
    if request.method == 'POST':
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        email = request.POST.get('email')
        if not email and not request.user.is_authenticated():
            return HttpResponse("Email Address is required.", status=453)
        if not subject:
            return HttpResponse("Subject is required.", status=451)
        if not body:
            return HttpResponse("Message is required.", status=452)
        form = form_class(request.POST, sender=request.user, request=request)
        if form.is_valid():
            form.save()
            return HttpResponse("")
        else:
            if email:
                if form['email'].errors:
                    return HttpResponse("Invalid Email Address.", status=453)
            if form['captcha'].errors:
                return HttpResponse("Captcha verification required.", status=454)
            return HttpResponse("Internal Error, try again later", status=500)
    return None


class FolderMixinOverride(FolderMixin):
    def get_context_data(self, **kwargs):
        context = super(FolderMixinOverride, self).get_context_data(**kwargs)
        p = Paginator(context['pm_messages'], 25)
        page = get_request_param(self.request, 'page', default='1')
        order_by = (get_request_param(self.request, 'o', None))
        try:
            context.update({'pm_messages': p.page(page), 'paginator': p, 'order_by': order_by})
        except PageNotAnInteger:
            context.update({'pm_messages': p.page(1), 'paginator': p, 'order_by': order_by})
        except EmptyPage:
            context.update({'pm_messages': p.page(p.num_pages), 'paginator': p, 'order_by': order_by})
        return context


class InboxView(FolderMixinOverride, TemplateView):
    folder_name = 'inbox'
    view_name = 'inbox'
    template_name = 'postman/inbox.html'


inbox_override = login_required(verified_email_required(InboxView.as_view()))


class SentView(FolderMixinOverride, TemplateView):
    folder_name = 'sent'
    view_name = 'sent'
    template_name = 'postman/sent.html'


sent_override = login_required(verified_email_required(SentView.as_view()))


class ArchivesView(FolderMixinOverride, TemplateView):
    folder_name = 'archives'
    view_name = 'archives'
    template_name = 'postman/archives.html'


archives_override = login_required(verified_email_required(ArchivesView.as_view()))


class TrashView(FolderMixinOverride, TemplateView):
    folder_name = 'trash'
    view_name = 'trash'
    template_name = 'postman/trash.html'


trash_override = login_required(verified_email_required(TrashView.as_view()))


class WriteViewOverride(WriteView):
    form_classes = (WriteFormOverride, AnonymousWriteFormOverride)

    def get_success_url(self):
        if self.request.GET.get('next'):
            return self.request.GET.get('next')
        elif self.request.user.is_authenticated():
            return 'inbox'
        return 'message_sent'

    def get_form_kwargs(self):
        kwargs = super(WriteViewOverride, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(WriteViewOverride, self).get_context_data(**kwargs)
        recipient = self.kwargs.get('recipients')
        if recipient:
            user = get_user_model().objects.get(name=recipient)
            try:
                if user.userprofile.is_mechanic:
                    context['mech_id'] = user.userprofile.pk
                context['name'] = user.userprofile.name
                context['thumb'] = get_thumbnail_url_from_user(user)
            except Exception:
                pass
        return context


write_override = WriteViewOverride.as_view()


class ReplyViewOverride(ReplyView):
    form_class = FullReplyFormOverride

    def get_success_url(self):
        return self.request.GET.get('next') or 'inbox'

    def get_initial(self):
        self.initial = super(ReplyViewOverride, self).get_initial()
        if self.request.method == 'GET':
            self.initial.update({"body": ""})
        return self.initial

    def get_form_kwargs(self):
        kwargs = super(ReplyViewOverride, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ReplyViewOverride, self).get_context_data(**kwargs)
        try:
            if self.parent.sender.userprofile.is_mechanic:
                context['mech_id'] = self.parent.sender.userprofile.pk
            context['name'] = self.parent.sender.userprofile.name
            context['thumb'] = get_thumbnail_url_from_user(self.parent.sender)
        except Exception:
            if self.parent.sender:
                if self.parent.sender.userprofile.name:
                    context['name'] = self.parent.sender.userprofile.name
                else:
                    context['name'] = 'Anonymous'
            else:
                context['name'] = self.parent.obfuscated_sender
        return context


reply_override = login_required(verified_email_required(ReplyViewOverride.as_view()))


def message_sent(request):
    return render(request, "postman/done.html", {})


class ReviewView(CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review.html'

    def __init__(self, **kwargs):
        super(ReviewView, self).__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        next_url = get_next_redirect_url(self.request, 'next')
        if next_url:
            return "%s" % next_url
        else:
            return reverse_lazy('browse')

    def get_context_data(self, **kwargs):
        context = super(ReviewView, self).get_context_data(**kwargs)
        if self.request.user.userprofile.is_mechanic:
            context['is_mechanic'] = True
            return context
        if self.request.user.userprofile.review_points <= 0:
            context['no_points'] = True
            return context
        mechanic = get_user_model().objects.get(name=get_request_param(self.request, 'mech_id')).pk
        reviewed = Review.objects.filter(user=self.request.user, mechanic=mechanic)
        if reviewed:
            context['reviewed'] = True
            return context
        recipient = get_request_param(self.request, 'mech_id')
        if recipient:
            try:
                context['mech_id'] = recipient
                context['name'] = UserProfile.objects.get(user__name=recipient).name
                context['thumb'] = UserProfile.objects.get(user__name=recipient).avatar_thumbnail.url
            except Exception:
                pass
        return context

    def post(self, request, *args, **kwargs):
        if request.user.userprofile.is_mechanic:
            return redirect(reverse_lazy('browse'))
        if request.user.userprofile.review_points <= 0:
            return redirect(reverse_lazy('browse'))
        mechanic = get_user_model().objects.get(name=get_request_param(self.request, 'mech_id')).pk
        reviewed = Review.objects.filter(user=self.request.user, mechanic=mechanic)
        if reviewed:
            return redirect(reverse_lazy('browse'))
        return super(ReviewView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ReviewView, self).get_form_kwargs()
        if self.request.method == 'POST':
            post = kwargs['data'].copy()  # self.request.POST is immutable
            post['mechanic'] = get_user_model().objects.get(name=get_request_param(self.request, 'mech_id')).pk
            post['user'] = self.request.user.pk
            kwargs['data'] = post
        return kwargs


review = login_required(verified_mobile_required(ReviewView.as_view()))


def ajax_get_reviews(request):
    try:
        pk = int(request.POST.get('id_pk').strip(' "'))
        page = int(request.POST.get('page').strip(' "'))
        reviews = list(reversed(
            Review.objects.filter(mechanic=pk, comment__isnull=False, comment__gt='').values_list('rating', 'comment',
                                                                                                  'user')))
        p = Paginator(reviews, 5)
        last = p.num_pages == page
        result = {"reviews": [
            {"rating": int((x[0] / 5) * 100), "comment": x[1],
             "user": get_name_icon(get_user_model().objects.get(pk=x[2]))} for x in p.page(page)], "last": last}
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


class AjaxableResponseMixin(object):
    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response


class AjaxPostAJobMixin(AjaxableResponseMixin):
    model = PostAJob
    form_class = PostAJobForm
    success_url = '/posts/'

    def get_form_kwargs(self):
        kwargs = super(AjaxPostAJobMixin, self).get_form_kwargs()
        if self.request.method == 'POST':
            post = kwargs['data'].copy()  # self.request.POST is immutable
            post['user'] = self.request.user.pk
            kwargs['data'] = post
        return kwargs


class AjaxPostAJobView(AjaxPostAJobMixin, CreateView):
    template_name = 'post.html'

    def post(self, request, *args, **kwargs):
        if self.request.user.postajob.filter(done=False).count() >= 5:
            result = {"__all__": ["You can only have 5 active posts. Clean up any active posts you may have."]}
            return JsonResponse(result, status=400)
        return super(AjaxPostAJobView, self).post(request, *args, **kwargs)


ajax_post_a_job = login_required(verified_email_required(AjaxPostAJobView.as_view()))


class AjaxUpdatePostView(AjaxPostAJobMixin, UpdateView):
    def get(self, request, *args, **kwargs):
        post = self.get_object()
        result = {"latitude": post.latitude, "longitude": post.longitude, "car_make": post.car_make,
                  "car_model": post.car_model, "car_year": post.car_year, "skill": post.skill.pk,
                  "comment": post.comment}
        return JsonResponse(result)

    def get_object(self, queryset=None):
        pk = ''
        if self.request.method == 'POST':
            pk = self.request.POST.get('pk')
        if self.request.method == 'GET':
            pk = get_request_param(self.request, 'pk')
        return PostAJob.objects.get(pk=pk)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            if obj.user != self.request.user:
                return HttpResponse("Request Denied.", status=404)
            if obj.done:
                return HttpResponse("Request Denied.", status=404)
            return super(AjaxUpdatePostView, self).dispatch(request, *args, **kwargs)
        except Exception:
            print(traceback.format_exc())
            return HttpResponse("Request Denied.", status=404)


ajax_update_post = login_required(verified_email_required(AjaxUpdatePostView.as_view()))


@login_required
@verified_email_required
def ajax_get_posts(request):
    try:
        posts = request.user.postajob.values_list('pk', 'comment', 'done', 'timestamp')[:25]
        result = {
            "posts": [{"pk": x[0], "comment": x[1][:30], "status": x[2],
                       "date": compact_date(localtime(x[3]), "g:i A,M j,n/j/y")} for x in posts]}
        return JsonResponse(result)
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


@login_required
@verified_email_required
def ajax_mark_done(request):
    if request.method == 'POST':
        try:
            pk = request.POST.get('pk')
            post = PostAJob.objects.get(pk=pk)
            if post.user != request.user:
                return HttpResponse("Request Denied.", status=404)
            else:
                post.done = True
                post.save()
            return HttpResponse("")
        except Exception:
            print(traceback.format_exc())
    return HttpResponse("Internal Error, try again later", status=500)


class BrowseRequestsView(ListView):
    template_name = 'mechanics/browse_requests.html'
    model = PostAJob

    def get_context_data(self, **kwargs):
        context = super(BrowseRequestsView, self).get_context_data(**kwargs)
        try:
            query_default = str(self.request.user.location.latitude) + ',' + str(self.request.user.location.longitude)
        except Exception:
            query_default = ''
        query = get_request_param(self.request, 'query', default=query_default)
        request_id = get_request_param(self.request, 'request_id', default='')
        skill = get_request_param(self.request, 'skill', default='')
        context['query'] = query
        context['request_id'] = request_id
        context['skill'] = skill
        context['skillChoice'] = SkillChoice.objects.all()
        return context


browse_requests_view = profile_complete_required(BrowseRequestsView.as_view())


@profile_complete_required
def ajax_get_request_markers(request):
    try:
        sw_lat = float(request.POST.get('id_sw_lat').strip(' "'))
        sw_lng = float(request.POST.get('id_sw_lng').strip(' "'))
        ne_lat = float(request.POST.get('id_ne_lat').strip(' "'))
        ne_lng = float(request.POST.get('id_ne_lng').strip(' "'))
        skill = request.POST.get('id_skill')
        requests_list = get_requests_list(sw_lat, sw_lng, ne_lat, ne_lng, skill)
        result = [
            {"pk": x[0], "latlng": (x[1], x[2]), "icon": get_icon_url_from_user(get_user_model().objects.get(pk=x[3]))}
            for x in requests_list]
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


@profile_complete_required
def ajax_get_requests_nearest(request):
    try:
        lat = float(request.POST.get('id_lat').strip(' "'))
        lng = float(request.POST.get('id_lng').strip(' "'))
        skill = request.POST.get('id_skill')
        requests_nearest = get_requests_nearest(lat, lng, skill)
        result = [
            {"pk": x[0], "name": x[1], "miles": x[2], "description": x[3], "icon": x[4], "skill": x[5], "car": x[6]} for
            x in requests_nearest]
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


@profile_complete_required
def ajax_get_request(request):
    try:
        x = get_request(int(request.POST.get('id_pk')))
        result = {"id": x[0], "name": x[1], "description": x[2], "thumbnail": x[3], "skill": x[4], "car": x[5],
                  "captcha": check_send_rate(request)}
        return HttpResponse(simplejson.dumps(result), content_type="application/json")
    except Exception:
        print(traceback.format_exc())
        return HttpResponse("Internal Error, try again later", status=500)


@login_required
def update_avatar(request):
    form_class = AvatarUploadForm
    if request.method == 'POST':
        name = request.POST.get('name')
        short_bio = request.POST.get('short_bio')
        if name:
            if len(name) <= 255:
                request.user.userprofile.name = name
        if short_bio:
            if len(short_bio) < 160:
                request.user.userprofile.short_bio = short_bio
        request.user.userprofile.save()
        form = form_class(data=request.POST, instance=request.user.userprofile, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('profile_wizard') + "?page=1")
        else:
            return redirect(reverse_lazy('profile_wizard') + "?page=1")
    return HttpResponse("Request Denied.", status=404)
