from django.shortcuts import render, redirect, get_object_or_404
from authentication.models import User
from .models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule
from .forms import CharacterAccessForm, CorpAccessForm, AllianceAccessForm
from eveonline.managers import EVEManager
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
import logging

logger = logging.getLogger(__name__)

@login_required
def list_useraccess(request):
    logger.debug("list_access called by user %s" % request.user)
    ua = UserAccess.objects.filter(user=request.user)
    access = request.user.has_perm('access.site_access')
    return render(request, 'registered/access/useraccess.html', context={'useraccess':ua, 'access':access})

@login_required
def list_access_rules(request):
    logger.debug("list_access_rules called by user %s" % request.user)
    characcess = CharacterAccessRule.objects.all()
    corpaccess = CorpAccessRule.objects.all()
    allianceaccess = AllianceAccessRule.objects.all()
    context = {
        'characteraccess': characcess,
        'corpaccess': corpaccess,
        'allianceaccess': allianceaccess,
    }
    return render(request, 'registered/access/accessrules.html', context=context)

@login_required
@permission_required('access.site_access')
@permission_required('access.add_characteraccessrule')
def characteraccess_create(request):
    logger.debug("characteraccess_create called by user %s" % request.user)
    if request.method == 'POST':
        form = CharacterAccessForm(request.POST)
        logger.debug("Request type POST contains form, is valid: %s" % form.is_valid())
        if form.is_valid():
            character = EVEManager.get_character_by_id(form.cleaned_data['id'])
            if CharacterAccessRule.objects.filter(character=character).exists() is False:
                ca = CharacterAccessRule(character=character)
                logger.info("User %s creating access for %s" % (request.user, ca))
                ca.save()
            else:
                logger.warn("User %s attempting to duplicate access for %s" % character)
            return redirect('access_list_access_rules')
    else:
        form = CharacterAccessForm()
    return render(request, 'registered/access/create_form.html', context={'form': form, 'type': 'Character'})

@login_required
@permission_required('access.site_access')
@permission_required('access.delete_characteraccess')
def characteraccess_delete(request, ca_id):
    logger.debug("characteracces_delete called by user %s for ca_id %s" % (request.user, ca_id))
    ca = get_object_or_404(CharacterAccessRule, id=ca_id)
    logger.info("User %s removing access for %s" % (request.user, ca))
    ca.delete()
    return redirect('access_list_access_rules')

@login_required
@permission_required('access.site_access')
@permission_required('access.add_corpaccessrule')
def corpaccess_create(request):
    logger.debug("corpaccess_create called by user %s" % request.user)
    if request.method == 'POST':
        form = CorpAccessForm(request.POST)
        logger.debug("Request type POST contains form, is valid: %s" % form.is_valid())
        if form.is_valid():
            corp = EVEManager.get_corp_by_id(form.cleaned_data['id'])
            if CorpAccessRule.objects.filter(corp=corp).exists() is False:
                ca = CorpAccessRule(corp=corp)
                logger.info("User %s creating access for %s" % (request.user, ca))
                ca.save()
            else:
                logger.warn("User %s attempting to duplicate access for %s" % corp)
            return redirect('access_list_access_rules')
    else:
        form = CorpAccessForm()
    return render(request, 'registered/access/create_form.html', context={'form': form, 'type': 'Corporation'})

@login_required
@permission_required('access.site_access')
@permission_required('access.delete_corpaccessrule')
def corpaccess_delete(request, ca_id):
    logger.debug("corpaccess_delete called by user %s for ca_id %s" % (request.user, ca_id))
    ca = get_object_or_404(CorpAccessRule, id=ca_id)
    logger.info("User %s removing access for %s" % (request.user, ca))
    ca.delete()
    return redirect('access_list_access_rules')

@login_required
@permission_required('access.site_access')
@permission_required('access.add_allianceaccessrule')
def allianceaccess_create(request):
    logger.debug("allianceaccess_create called by user %s" % request.user)
    if request.method == 'POST':
        form = AllianceAccessForm(request.POST)
        logger.debug("Request type POST contains form, is valid: %s" % form.is_valid())
        if form.is_valid():
            alliance = EVEManager.get_alliance_by_id(form.cleaned_data['id'])
            if AllianceAccessRule.objects.filter(alliance=alliance).exists() is False:
                aa = AllianceAccessRule(alliance=alliance)
                logger.info("User %s creating access for %s" % (request.user, aa))
                aa.save()
            else:
                logger.warn("User %s attempting to duplicate access for %s" % alliance)
            return redirect('access_list_access_rules')
    else:
        form = AllianceAccessForm()
    return render(request, 'registered/access/create_form.html', context={'form': form, 'type': 'Alliance'})

@login_required
@permission_required('access.site_access')
@permission_required('access.delete_allianceaccessrule')
def allianceaccess_delete(request, aa_id):
    logger.debug("allianceaccess_delete called by user %s for aa_id %s" % (request.user, aa_id))
    aa = get_object_or_404(AllianceAccessRule, id=aa_id)
    logger.info("User %s removing access for %s" % (request.user, aa))
    aa.delete()
    return redirect('access_list_access_rules')


@login_required
@permission_required('access.site_access')
@permission_required('access.audit_access')
def view_character_access(request, ca_id):
    logger.debug("view_character_access called by user %s for characteraccessrule id %s" % (request.user, ca_id))
    ca = get_object_or_404(CharacterAccessRule, id=ca_id)
    ua = ca.access.all()
    return render(request, 'registered/access/viewrule.html', context={'type':'Character', 'rule':ca, 'useraccess':ua})

@login_required
@permission_required('access.site_access')
@permission_required('access.audit_access')
def view_corp_access(request, ca_id):
    logger.debug("view_character_access called by user %s for characteraccessrule id %s" % (request.user, ca_id))
    ca = get_object_or_404(CorpAccessRule, id=ca_id)
    ua = ca.access.all()
    return render(request, 'registered/access/viewrule.html', context={'type':'Corp', 'rule':ca, 'useraccess':ua})

@login_required
@permission_required('access.site_access')
@permission_required('access.audit_access')
def view_alliance_access(request, aa_id):
    logger.debug("view_character_access called by user %s for characteraccessrule id %s" % (request.user, aa_id))
    aa = get_object_or_404(AllianceAccessRule, id=aa_id)
    ua = aa.access.all()
    return render(request, 'registered/access/viewrule.html', context={'type':'Alliance', 'rule':aa, 'useraccess':ua})

@login_required
@permission_required('access.site_access')
@permission_required('acces.audit_access')
def recheck_access(request, ua_id):
    logger.debug("recheck_access called by user %s for useraccess id %s" % (request.user, ua_id))
    ua = get_object_or_404(UserAccess, id=ua_id)
    ua.verify()
    return redirect('access_list_access_rules')
