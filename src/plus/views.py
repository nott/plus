import datetime
import random

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils import translation
from django.contrib.auth import logout as auth_logout
from social_auth.views import auth as social_auth_begin

from models import Event, EventAttendance, LANG_CODES
from commonutils.decorators import render_to
from commonutils.social import socialize_user, socialize_users

@render_to('plus/home.html')
def home(request):
    return {}

def plus_socialauth_begin(request, backend):
    '''we want to logout before logging in as another user.'''
    auth_logout(request)
    return social_auth_begin(request, backend)

@render_to('plus/event.html')
def show_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    translation.activate(LANG_CODES[event.language])

    user = request.user
    
    attendances = list(EventAttendance.objects.filter(
            event=event).select_related('user'))

    goers = [a.user for a in attendances if \
                        user.id != a.user.id]
    random.shuffle(goers)
    goers = socialize_users(goers)
    goer_id_set = set(a.user.id for a in attendances)

    return {'Content-Language': translation.get_language(),
            'event': event,
            'curr_attendance': user.id in goer_id_set,
            'future_event': event.starts_at > datetime.datetime.now(),
            'goers': goers,
            'goer_id_set': goer_id_set}


def event_plus(request, slug):
    event = get_object_or_404(Event, slug=slug,
                              starts_at__gt=datetime.datetime.now())
    user = request.user
    goers_count = EventAttendance.objects.filter(event=event).count()

    if user.is_authenticated() and (not event.seats_number or \
                                        event.seats_number > goers_count):
        att_count = EventAttendance.objects.filter(
            event=event, user=user).count()
        if att_count == 0:
            EventAttendance(event=event, user=user).save()

    return redirect(reverse('show_event', args=[slug]))


def event_minus(request, slug):
    event = get_object_or_404(Event, slug=slug,
                              starts_at__gt=datetime.datetime.now())
    user = request.user

    if user.is_authenticated():
        EventAttendance.objects.filter(
                event=event, user=user).delete()
    return redirect(reverse('show_event', args=[slug]))

def anything_logout(request, url):
    """Logs user out"""
    auth_logout(request)
    return redirect('/' + url)

@render_to('autherror.html')
def auth_error(request):
    """Auth error view"""
    from social_auth import __version__ as version
    error_msg = request.session.pop(settings.SOCIAL_AUTH_ERROR_KEY, None)
    return {'version': version,
            'error_msg': error_msg}

@render_to('500.html')
def error500(request):
    """ Error 500 view """
    return {}
