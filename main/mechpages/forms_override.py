from builtins import super, len
from allauth.account.forms import AddEmailForm, ChangePasswordForm, SetPasswordForm, ResetPasswordKeyForm


class CustomAddEmailForm(AddEmailForm):
    def clean_email(self):
        value = super(CustomAddEmailForm, self).clean_email()
        if value:
            if len(value) > 255:
                self._errors['email'] = self.error_class(['Email is too long (max: 255 characters)'])
        return value


class CustomChangePasswordForm(ChangePasswordForm):
    def clean_password2(self):
        value = super(CustomChangePasswordForm, self).clean_password2()
        if value:
            if len(value) > 128:
                self._errors['password1'] = self.error_class(['Password is too long (max: 128 characters)'])


class CustomSetPasswordForm(SetPasswordForm):
    def clean_password2(self):
        value = super(CustomSetPasswordForm, self).clean_password2()
        if value:
            if len(value) > 128:
                self._errors['password1'] = self.error_class(['Password is too long (max: 128 characters)'])


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def clean_password2(self):
        value = super(CustomResetPasswordKeyForm, self).clean_password2()
        if value:
            if len(value) > 128:
                self._errors['password1'] = self.error_class(['Password is too long (max: 128 characters)'])