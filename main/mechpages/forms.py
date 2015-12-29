import json
import traceback
from captcha.fields import ReCaptchaField
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import CheckboxSelectMultiple
from django.forms.models import ModelChoiceField
from io import BytesIO
from builtins import len, super, Exception, int, float, str
from PIL import Image
from django import forms
from postman.forms import FullReplyForm, AnonymousWriteForm, WriteForm
from mechpages.util import check_send_rate, get_rating_average_and_count
from .models import UserProfile, MobileNumber, ProjectImage, JobHistory, Location, Review, PostAJob, SkillChoice

STATE_CHOICES = (
    ('-', 'State'), ('AL', 'AL'), ('AK', 'AK'), ('AZ', 'AZ'), ('AR', 'AR'), ('CA', 'CA'), ('CO', 'CO'), ('CT', 'CT'),
    ('DE', 'DE'), ('DC', 'DC'), ('FL', 'FL'), ('GA', 'GA'), ('HI', 'HI'), ('ID', 'ID'), ('IL', 'IL'), ('IN', 'IN'),
    ('IA', 'IA'), ('KS', 'KS'), ('KY', 'KY'), ('LA', 'LA'), ('ME', 'ME'), ('MD', 'MD'), ('MA', 'MA'), ('MI', 'MI'),
    ('MN', 'MN'), ('MS', 'MS'), ('MO', 'MO'), ('MT', 'MT'), ('NE', 'NE'), ('NV', 'NV'), ('NH', 'NH'), ('NJ', 'NJ'),
    ('NM', 'NM'), ('NY', 'NY'), ('NC', 'NC'), ('ND', 'ND'), ('OH', 'OH'), ('OK', 'OK'), ('OR', 'OR'), ('PA', 'PA'),
    ('RI', 'RI'), ('SC', 'SC'), ('SD', 'SD'), ('TN', 'TN'), ('TX', 'TX'), ('UT', 'UT'), ('VT', 'VT'), ('VA', 'VA'),
    ('WA', 'WA'), ('WV', 'WV'), ('WI', 'WI'), ('WY', 'WY'))


def _clean_img(self, name):
    img = self.cleaned_data.get(name)
    if img is not None:
        try:
            if img:
                if img.content_type not in ('image/jpeg', 'image/png', 'image/gif', 'image/mpo'):
                    self._errors[name] = self.error_class(['Only jpeg, png, and gif formats are supported.'])
                elif img.size > 10485760:
                    self._errors[name] = self.error_class(['Image file too large ( > 10mb )'])
                else:
                    return img
            else:
                self._errors[name] = self.error_class(["Couldn't read uploaded image"])
        except Exception:
            pass


def _crop_img(self, name):
    form_data = self.cleaned_data
    # Data from image-cropper on how to crop the image
    extra = form_data.get('image_extra')
    try:
        image = form_data.get(name)
        temp = Image.open(image)
        format = temp.format
        # Rotate image based off of exif data (used by mobile devices that automatically orients the picture)
        # http://www.lifl.fr/~damien.riquet/auto-rotating-pictures-using-pil.html
        try:
            exif = temp._getexif()
            orientation_key = 274
            if exif:
                if orientation_key in exif:
                    orientation = exif[orientation_key]
                    rotate_values = {3: 180, 6: 270, 8: 90}
                    if orientation in rotate_values:
                        temp = temp.rotate(rotate_values[orientation], expand=1)
        except Exception:
            pass
        extra = json.loads(extra)
        x = int(extra.get('x'))
        y = int(extra.get('y'))
        height = int(extra.get('height'))
        width = int(extra.get('width'))
        temp = temp.crop((x, y, x + width, y + height))
        # Django imagefield is a InMemoryUploadedFile, need to convert PIL image in order to save
        temp_io = BytesIO()
        temp.save(temp_io, format=format)
        temp_file = InMemoryUploadedFile(temp_io, None, image.name, 'image/' + format,
                                         temp_io.getbuffer().nbytes, None)
        self.cleaned_data[name] = temp_file
        return form_data
    except Exception:
        print(traceback.format_exc())
        self._errors[name] = self.error_class(['Unable to read image, try a different image'])


class SignUpForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)
    car_make = forms.CharField(max_length=50, required=False)
    car_model = forms.CharField(max_length=50, required=False)
    car_year = forms.CharField(max_length=4, required=False)
    address = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=50, required=False)
    state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
    zip = forms.CharField(max_length=10, required=False)

    def clean(self):
        email = self.cleaned_data.get('email')
        if email:
            if len(email) > 255:
                self._errors['email'] = self.error_class(['Email is too long (max: 255 characters)'])
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) > 128:
                self._errors['password1'] = self.error_class(['Password is too long (max: 128 characters)'])

    def signup(self, request, user):
        user.userprofile.name = self.cleaned_data.get('name')
        user.userprofile.car_make = self.cleaned_data['car_make']
        user.userprofile.car_model = self.cleaned_data['car_model']
        user.userprofile.car_year = self.cleaned_data['car_year']
        user.userprofile.address = self.cleaned_data['address']
        user.userprofile.city = self.cleaned_data['city']
        user.userprofile.state = self.cleaned_data['state']
        user.userprofile.zip = self.cleaned_data['zip']
        user.userprofile.save()
        user.save()


class UpdateUserProfileForm(forms.ModelForm):
    image_extra = forms.CharField(widget=forms.HiddenInput(), max_length=255, required=False)

    def clean_avatar(self):
        img = _clean_img(self, name='avatar')
        if img:
            return img

    def clean(self):
        if self.cleaned_data.get('avatar'):
            _crop_img(self, 'avatar')

    class Meta:
        model = UserProfile
        fields = ('name', 'avatar', 'address', 'city', 'state', 'zip', 'car_make', 'car_model', 'car_year',
                  'image_extra')


class UpdateMechanicProfileForm(forms.ModelForm):
    name = forms.CharField(max_length=255, required=True)
    image_extra = forms.CharField(widget=forms.HiddenInput(), max_length=255, required=False)

    def clean_avatar(self):
        img = _clean_img(self, name='avatar')
        if img:
            return img

    def clean(self):
        if self.cleaned_data.get('avatar'):
            _crop_img(self, 'avatar')

    class Meta:
        model = UserProfile
        fields = ('name', 'avatar', 'car_make', 'car_model', 'car_year', 'image_extra')


class VerifyPinForm(forms.ModelForm):
    pin = forms.CharField(max_length=5, required=True)

    class Meta:
        model = MobileNumber
        fields = ('pin', 'mobile')


class ProfileWizardForm1(forms.ModelForm):
    name = forms.CharField(max_length=255, required=True)
    short_bio = forms.CharField(widget=forms.Textarea, max_length=160, required=True)

    def clean(self):
        if not self.instance.user.userprofile.avatar:
            raise forms.ValidationError("You must provide a profile picture.")

    class Meta:
        model = UserProfile
        fields = ('name', 'short_bio')


class AvatarUploadForm(forms.ModelForm):
    image_extra = forms.CharField(widget=forms.HiddenInput(), max_length=255, required=False)

    def clean_avatar(self):
        img = _clean_img(self, name='avatar')
        if img:
            return img

    def clean(self):
        if self.cleaned_data.get('avatar'):
            _crop_img(self, 'avatar')

    class Meta:
        model = UserProfile
        fields = ('avatar', 'image_extra')


class ProfileWizardForm2JobHistory(forms.ModelForm):
    # Passing in extra data from the view.  If required is set to true, the form must be filled.
    # (http://stackoverflow.com/questions/5806224/sending-request-user-object-to-modelform-from-class-based-generic-view-in-django)
    def __init__(self, *args, **kwargs):
        self.required = kwargs.pop('required', None)
        super(ProfileWizardForm2JobHistory, self).__init__(*args, **kwargs)

    def clean_years(self):
        years = self.cleaned_data.get('years')
        if years:
            if not years.isdigit():
                self._errors['years'] = self.error_class(['Invalid year. (Ex: 2015)'])
        return years

    # The 'company', 'position', and 'years' field will be required if 'required' is set to true.  They will also be
    # required if any of the fields are filled in.  The variable 'required' is set by the view based on the the name of
    # the form submit button (ex: if form submit is 'page2', then required is true, if form submit is 'page2next', then
    # false. If 'required' is None, then it must mean that the user clicked either the next or prev button.  In this
    # case, I want to make sure the user has at least one job history before proceeding with the wizard.
    def clean(self):
        company = self.cleaned_data.get('company')
        position = self.cleaned_data.get('position')
        years = self.cleaned_data.get('years')
        description = self.cleaned_data.get('description')
        if self.required or company or position or years or description:
            if not company:
                self._errors['company'] = self.error_class(['The company field is required.'])
            if not position:
                self._errors['position'] = self.error_class(['The position field required.'])
            if not years:
                self._errors['years'] = self.error_class(['The years field is required.'])
        if not self.required:
            if self.instance.user.jobhistory.count() < 1:
                raise forms.ValidationError("Please fill in at least 1 work history before proceeding.")

    def save(self, *args, **kwargs):
        company = self.cleaned_data.get('company')
        position = self.cleaned_data.get('position')
        years = self.cleaned_data.get('years')
        description = self.cleaned_data.get('description')
        if company and position and years:
            job_history = JobHistory(user=self.instance.user, company=company, position=position, years=years,
                                     description=description)
            job_history.save()

    class Meta:
        model = JobHistory
        fields = ('company', 'position', 'years', 'description')


class ProfileWizardForm2Skills(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # the 'required' is for ProfileWizardForm2JobHistory and is not needed here, if un-popped, it will throw
        # an exception saying it is unexpected
        kwargs.pop('required', None)
        super(ProfileWizardForm2Skills, self).__init__(*args, **kwargs)

    class Meta:
        model = UserProfile
        fields = ('skills',)
        widgets = {
            'skills': CheckboxSelectMultiple,
        }


class ProfileWizardForm3(forms.ModelForm):
    image_extra = forms.CharField(widget=forms.HiddenInput(), max_length=255, required=False)

    def clean_image(self):
        user = self.instance.user
        if user.projectimages.count() >= user.userprofile.project_limit:
            self._errors['image'] = self.error_class(['Maximum number of photos reached.'])
        img = _clean_img(self, name='image')
        if img:
            return img

    def clean(self):
        _crop_img(self, 'image')

    def save(self, *args, **kwargs):
        title = self.cleaned_data.get('title')
        image = self.cleaned_data.get('image')
        description = self.cleaned_data.get('description')
        project_image = ProjectImage(user=self.instance.user, title=title, image=image, description=description)
        project_image.save()

    class Meta:
        model = ProjectImage
        fields = ('title', 'image', 'description', 'image_extra')


class ProfileWizardForm4(forms.ModelForm):
    def clean(self):
        latitude = self.cleaned_data.get('latitude')
        longitude = self.cleaned_data.get('longitude')
        radius = self.cleaned_data.get('radius')
        if not latitude or not longitude or not radius:
            raise forms.ValidationError("Please select an area you wish to work at")
        if float(radius) > 100000:
            raise forms.ValidationError("Please reduce your selected radius")

    def save(self, *args, **kwargs):
        try:
            location = Location.objects.get(user=self.instance.user)
        except Exception:
            location = None
        latitude = self.cleaned_data['latitude']
        longitude = self.cleaned_data['longitude']
        radius = self.cleaned_data['radius']
        if not location:
            location = Location(user=self.instance.user, latitude=latitude, longitude=longitude, radius=radius)
            location.save()
        if location:
            location.latitude = latitude
            location.longitude = longitude
            location.radius = radius
            location.save()

    class Meta:
        model = Location
        fields = ('latitude', 'longitude', 'radius')
        widgets = {
            'latitude': forms.HiddenInput,
            'longitude': forms.HiddenInput,
            'radius': forms.HiddenInput,
        }


class ProfileWizardForm5(forms.ModelForm):
    def clean(self):
        try:
            self.instance.user.location
        except Exception:
            raise forms.ValidationError("A location must be selected to proceed.")
        if not self.instance.user.userprofile.avatar:
            raise forms.ValidationError("You must provide a profile picture to proceed.")
        if not self.instance.user.userprofile.name:
            raise forms.ValidationError("You must provide a name to proceed.")
        if not self.instance.user.userprofile.short_bio:
            raise forms.ValidationError("You must provide a short bio to proceed.")
        if self.instance.user.jobhistory.count() == 0:
            raise forms.ValidationError("You must provide at least 1 work history to proceed.")

    def save(self, *args, **kwargs):
        self.instance.user.userprofile.profile_complete = True
        self.instance.user.userprofile.save()

    class Meta:
        model = UserProfile
        fields = ('profile_complete', 'publish')


class WriteFormOverride(WriteForm):
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(WriteFormOverride, self).__init__(*args, **kwargs)
        self.fields['body'].label = "Message"

    def clean(self):
        super(WriteFormOverride, self).clean()
        if check_send_rate(self.request, True) and 'captcha' in self._errors:
            del self._errors['captcha']
        return self.cleaned_data


class AnonymousWriteFormOverride(AnonymousWriteForm):
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AnonymousWriteFormOverride, self).__init__(*args, **kwargs)
        self.fields['body'].label = "Message"

    def clean(self):
        super(AnonymousWriteFormOverride, self).clean()
        if check_send_rate(self.request, True) and 'captcha' in self._errors:
            del self._errors['captcha']
        return self.cleaned_data


class FullReplyFormOverride(FullReplyForm):
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(FullReplyFormOverride, self).__init__(*args, **kwargs)
        self.fields['body'].label = "Message"

    def clean(self):
        super(FullReplyFormOverride, self).clean()
        if check_send_rate(self.request, True) and 'captcha' in self._errors:
            del self._errors['captcha']
        return self.cleaned_data


class ReviewForm(forms.ModelForm):
    def clean(self):
        super(ReviewForm, self).clean()
        rating = self.cleaned_data['rating']
        if rating == 0:
            self._errors['rating'] = self.error_class(['This field is required.'])

    def save(self, *args, **kwargs):
        result = super(ReviewForm, self).save()
        mechanic = self.cleaned_data.get('mechanic')
        rating = get_rating_average_and_count(mechanic)
        mechanic.userprofile.rating = rating[0]
        mechanic.userprofile.rating_count = rating[1]
        mechanic.userprofile.save()
        self.instance.user.userprofile.review_points -= 1
        self.instance.user.userprofile.save()
        return result

    class Meta:
        model = Review
        fields = ('mechanic', 'user', 'rating', 'comment')


class PostAJobForm(forms.ModelForm):
    skill = ModelChoiceField(queryset=SkillChoice.objects.all(), empty_label=None)

    def __init__(self, *args, **kwargs):
        super(PostAJobForm, self).__init__(*args, **kwargs)
        # set initial skill to general
        self.initial['skill'] = '11'

    def clean_car_year(self):
        car_year = self.cleaned_data.get('car_year')
        if car_year:
            if not car_year.isdigit() or len(car_year) < 4:
                self._errors['car_year'] = self.error_class(['Invalid year. (Ex: 2015)'])
        return car_year

    class Meta:
        model = PostAJob
        fields = ('user', 'longitude', 'latitude', 'car_make', 'car_model', 'car_year', 'comment', 'skill')


class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    message = forms.CharField(required=True, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Your name:"
        self.fields['email'].label = "Your email:"
        self.fields['message'].label = "What do you want to say?"
