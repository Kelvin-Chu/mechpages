from django.conf.urls import include, url
from django.contrib import admin
from postman import OPTIONS

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'mechpages.views.initial_home', name='initial_home'),
    url(r'^home/$', 'mechpages.views.home', name='home'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^accounts/password/change/$', 'mechpages.views.login_after_password_change', name='account_change_password'),
    url(r'^accounts/password/set/$', 'mechpages.views.login_after_password_set', name='account_set_password'),
    url(r"^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        'mechpages.views.password_reset_from_key', name="account_reset_password_from_key"),
    url(r"^accounts/email/$", 'mechpages.views.custom_email', name='account_email'),
    url(r'^accounts/verify-mobile/send_pin$', 'mechpages.views.ajax_send_pin', name='ajax_send_pin'),
    url(r'^accounts/verify-mobile/$', 'mechpages.views.ajax_verify_pin', name='ajax_verify_pin'),
    url(r'^accounts/verify-mobile/(?P<mechanic>mechanic)$', 'mechpages.views.ajax_verify_pin', name='ajax_verify_pin'),
    url(r'^accounts/convert/$', 'mechpages.views.mconvert', name='mechanic_convert'),
    url(r'^accounts/update-avatar/$', 'mechpages.views.update_avatar', name='update_avatar'),
    url(r'^accounts/profile/$', 'mechpages.views.update_profile_user', name='profile_user'),
    url(r'^accounts/profile/(?P<success>success)$', 'mechpages.views.update_profile_user', name='profile_user'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^messages/inbox/$', 'mechpages.views.inbox_override', name='inbox'),
    url(r'^messages/inbox/(?:(?P<option>' + OPTIONS + ')/)?$', 'mechpages.views.inbox_override', name='inbox'),
    url(r'^messages/sent/$', 'mechpages.views.sent_override', name='sent'),
    url(r'^messages/sent/(?:(?P<option>' + OPTIONS + ')/)?$', 'mechpages.views.sent_override', name='sent'),
    url(r'^messages/archive/$', 'mechpages.views.archives_override', name='archives'),
    url(r'^messages/archives/(?:(?P<option>' + OPTIONS + ')/)?$', 'mechpages.views.archives_override', name='archives'),
    url(r'^messages/trash/$', 'mechpages.views.trash_override', name='trash'),
    url(r'^messages/trash/(?:(?P<option>' + OPTIONS + ')/)?$', 'mechpages.views.trash_override', name='trash'),
    url(r'^messages/write/(?:(?P<recipients>[^/#]+)/)?$', 'mechpages.views.write_override', name='write'),
    url(r'^messages/reply/(?P<message_id>[\d]+)/$', 'mechpages.views.reply_override', name='reply'),
    url(r'^messages/done/$', 'mechpages.views.message_sent', name='message_sent'),
    url(r'^messages/', include('postman.urls', namespace='postman', app_name='postman')),
    url(r'^browse/$', 'mechpages.views.browse', name='browse'),
    # the following seven browse urls are hard coded into browse.js
    url(r'^browse/get-mechanics/$', 'mechpages.views.ajax_get_mechanics', name='ajax_get_mechanics'),
    url(r'^browse/get-mechanics-nearest/$', 'mechpages.views.ajax_get_mechanics_nearest',
        name='ajax_get_mechanics_list'),
    url(r'^browse/get-mechanic-profile/$', 'mechpages.views.ajax_get_mechanic_profile',
        name='ajax_get_mechanic_profile'),
    url(r'^browse/subscribe/$', 'mechpages.views.ajax_subscribe_availability', name='ajax_subscribe_availability'),
    url(r'^browse/sendmessage/$', 'mechpages.views.ajax_send_message', name='ajax_send_message'),
    url(r'^browse/review/$', 'mechpages.views.review', name='review'),
    url(r'^browse/get-reviews/$', 'mechpages.views.ajax_get_reviews', name='get_reviews'),
    # the following four post urls are hard coded into post.js and browse.js
    url(r'^posts/$', 'mechpages.views.ajax_post_a_job', name='post_a_job'),
    url(r'^posts/get-posts/$', 'mechpages.views.ajax_get_posts', name='ajax_get_posts'),
    url(r'^posts/update-post/$', 'mechpages.views.ajax_update_post', name='ajax_update_post'),
    url(r'^posts/mark-done/$', 'mechpages.views.ajax_mark_done', name='ajax_mark_done'),
    url(r'^mechanics/register/$', 'mechpages.views.mechanic_signup', name='mechanic_signup'),
    url(r'^mechanics/profile/$', 'mechpages.views.update_profile_mechanic', name='profile_mechanic'),
    url(r'^mechanics/profile/(?P<success>success)$', 'mechpages.views.update_profile_mechanic',
        name='profile_mechanic'),
    url(r'^mechanics/profile/(?P<msuccess>msuccess)$', 'mechpages.views.update_profile_mechanic',
        name='profile_mechanic'),
    url(r'^mechanics/tools/$', 'mechpages.views.tools', name='tools'),
    url(r"^mechanics/delete/$", 'mechpages.views.delete', name='delete'),
    url(r"^mechanics/remove-skill/$", 'mechpages.views.remove_skill', name='remove_skill'),
    url(r"^mechanics/add-skills/$", 'mechpages.views.add_skills', name='add_skills'),
    url(r'^mechanics/tools/profile-wizard/$', 'mechpages.views.profile_wizard', name='profile_wizard'),
    url(r'^mechanics/tools/browse_requests/$', 'mechpages.views.browse_requests_view', name='browse_requests'),
    url(r'^mechanics/tools/browse_requests/get-request-markers/$', 'mechpages.views.ajax_get_request_markers',
        name='ajax_get_request_markers'),
    url(r'^mechanics/tools/browse_requests/get-requests-nearest/$', 'mechpages.views.ajax_get_requests_nearest',
        name='ajax_get_requests_nearest'),
    url(r'^mechanics/tools/browse_requests/get-request/$', 'mechpages.views.ajax_get_request', name='ajax_get_request'),
    url(r'^mechanics/profile-required/$', 'mechpages.views.profile_required', name='profile_required'),
    url(r'^403/$', 'mechpages.views.not_allowed', name='not_allowed'),
    url(r'^terms-of-use/$', 'mechpages.views.terms_of_use', name='terms_of_use'),
    url(r'^privacy-policy/$', 'mechpages.views.privacy_policy', name='privacy_policy'),
    url(r'^contact/$', 'mechpages.views.contact', name='contact'),
    url(r'^contact/success$', 'mechpages.views.contact_success', name='contact_success'),
]
