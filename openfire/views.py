from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from .forms import OpenfireServiceAddForm
from .models import OpenfireService

@login_required
@permission_required('access.site_access')
def openfireservice_list(request):
    logger.debug("openfireservice_list called by user %s" % request)
    of = OpenfireService.objects.all()
    return render(request, 'registered/openfire/list.html', context={'services': of})

@login_required
@permission_required('access.site_access')
@permission_required('openfire.add_openfireservice')
def openfireservice_add(request):
    logger.debug("openfireservice_add called by user %s" % request.user)
    if request.method == "POST":
        form = OpenfireServiceAddForm(request.POST)
        if form.is_valid():
            if OpenfireService.objects.filter(restapi_address=form.cleaned_data['restapi_address']).exists() is False:
                service = OpenfireService()
                service.restapi_address = form.cleaned_data['restapi_address']
                service.restapi_secret_key = form.cleaned_data['restapi_secret_key']
                service.address = form.cleaned_data['address']
                service.port = form.cleaned_data['port']
                service.save()
                logger.info("User %s creating Openfire service %s" % (request.user, service))
            else:
                logger.warn("User %s attempting to duplicate Openfire service at %s" % (request.user, form.cleaned_data['restapi_address']))
            return redirect('openfire_service_list')
    else:
        form = OpenfireServiceAddForm()
    return render(request, 'registered/openfire/create_form.html', context={'form': form})

@login_required
@permission_required('access.site_access')
@permission_required('openfire.change_openfireservice')
def openfireservice_change(request, service_id):
    logger.debug("openfireservice_change called by user %s for service_id %s" % (request.user, service_id))
    service = get_object_or_404(OpenfireService, id=service_id)
    if request.method == 'POST':
        form = OpenfireServiceAddForm(request.POST)
        if form.is_valid():
            restapi_address = form.cleaned_data['restapi_address']
            restapi_secret_key = form.cleaned_data['restapi_secret_key']
            address = form.cleaned_data['address']
            port = form.cleaned_data['port']
            update_fields = []
            if service.restapi_address != restapi_address:
                update_fields.append('restapi_address')
                service.restapi_address = restapi_address
            if service.restapi_secret_key != restapi_secret_key:
                update_fields.append('restapi_secret_key')
                service.restapi_secret_key = restapi_secret_key
            if service.address != address:
                update_fields.append('address')
                service.address = address
            if service.port != port:
                update_fields.append('port')
                service.port = port
            if update_fields:
                logger.info("User %s updating OpenfireService %s fields %s" % (request.user, service, update_fields))
                service.save(update_fields=update_fields)
            else:
                logger.debug("Detected no changes between OpenfireService %s and supplied form" % service)
            return redirect('openfire_service_list')               
    else:
        data = {
            'restapi_address': service.restapi_address,
            'restapi_secret_key': service.restapi_secret_key,
            'address': service.address,
            'port': service.port,
        }
        form = OpenfireServiceAddForm(initial=data)
    return render(request, 'registered/openfire/create_form.html', context={'form': form})

@login_required
@permission_required('access.site_access')
@permission_required('openfire.delete_openfireservice')
def openfireservice_delete(request, service_id):
    logger.debug("openfireservice_delete called by user %s for service_id %s" % (request.user, service_id))
    service = get_object_or_404(OpenfireService, id=service_id)
    logger.info("User %s deleting Openfire service %s" % (request.user, service))
    service.delete()
    return redirect('openfire_service_list')
