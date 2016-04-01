from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from .models import MumbleService
from services.forms import ServicePasswordForm
import services.errors
import logging

logger = logging.getLogger(__name__)

@login_required
@permission_required('access.site_access')
def mumble_list(request):
    logger.debug("mumble_list called by user %s" % request.user)
    m = {ms:ms.get_display_parameters(request.user) for ms in MumbleService.objects.all() if ms.check_user_has_access(request.user)}
    logger.debug(m)
    return render(request, 'registered/services/list.html', context={'services': m, 'type': 'Mumble'})

@login_required
@permission_required('access.site_access')
def mumble_activate(request, mumble_id):
    logger.debug("mumble_activate called by user %s for mumble_id %s" % (request.user, mumble_id))
    m = get_object_or_404(MumbleService, pk=mumble_id)
    try:
        credentials = m.add_user(request.user)
        return render(request, 'registered/services/credentials.html', context={'credentials':credentials, 'next': 'mumble_list'})
    except services.errors.RequiredGroupsError:
        logger.warn("User %s not authorized to activate mumble %s" % (request.user, m))
    return rediect('mumble_list')

@login_required
@permission_required('access.site_access')
def mumble_deactivate(request, mumble_id):
    logger.debug("mumble_deactivate called by user %s for mumble_id %s" % (request.user, mumble_id))
    m = get_object_or_404(MumbleService, pk=mumble_id)
    try:
        m.remove_user(request.user)
    except services.errors.UserNotActiveError:
        logger.warn("Unable to deactivate user %s mumble %s - user does not have account on service" % (request.user, m))
    return redirect('mumble_list')

@login_required
@permission_required('access.site_access')
def mumble_password(request, mumble_id):
    logger.debug("mumble_password called by user %s for mumble_id %s" % (request.user, mumble_id))
    m = get_object_or_404(MumbleService, pk=mumble_id)
    try:
        if request.method == "POST":
            form = ServicePasswordForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['password']
                credentials = m.set_password(request.user, password)
                return render(request, 'registered/services/credentials.html', context={'credentials':credentials, 'next': 'mumble_list'})
        else:
            form = ServicePasswordForm()
        return render(request, 'public/form.html', context={'title': m.name, 'form': form, 'button_text':'Submit'})
    except services.errors.UserNotActiveError:
        logger.warn("Unable to deactivate user %s mumble %s - user does not have account on service" % (request.user, m))
    return rediect('mumble_list')
