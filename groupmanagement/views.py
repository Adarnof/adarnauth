from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import Group
from authentication.models import User
from forms import GroupAddForm, GroupEditForm, GroupTransferForm, AutoGroupForm
from models import GroupApplication, ExtendedGroup, AutoGroup
from access.models import CharacterAccessRule, CorpAccessRule, AllianceAccessRule
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
import logging

logger = logging.getLogger(__name__)

@login_required
@permission_required('access.site_access')
def group_list(request):
    logger.debug("group_list_view called by user %s" % request.user)
    applications = GroupApplication.objects.get_open().filter(user=request.user)
    applied = [a.extended_group for a in applications]
    owned = request.user.owned_groups.all()
    admin = request.user.admin_groups.all()
    auto = []
    user_groups = []
    for g in request.user.groups.all():
        if ExtendedGroup.objects.filter(group=g).exists():
            user_groups.append(ExtendedGroup.objects.get(group=g))
        if AutoGroup.objects.filter(group=g).exists():
            auto.append(AutoGroup.objects.get(group=g))
    all_groups = [g for g in list(ExtendedGroup.objects.all()) if g not in user_groups and g not in applied]
    logger.debug("User has groups %s" % user_groups)
    member = []
    for g in user_groups:
        if g in owned:
            member.append((g, False))
        elif g in admin:
            member.append((g, False))
        else:
            member.append((g, True))
    logger.debug("Groups available: %s" % all_groups)
    available = list(all_groups)
    for g in all_groups:
        logger.debug("Checking %s" % g)
        if g.hidden:
            logger.debug("Removing %s as is hidden." % g)
            available.remove(g)
        elif g.parent:
            if g.parent not in user_groups:
                logger.debug("Removing %s as user lacks parent." % g)
                available.remove(g)
    logger.debug("Collected %s member %s available %s applied groups for user %s" % (len(member), len(available), len(applied), request.user))
    context = {
        'member': member,
        'applications': applications,
        'available': available,
        'auto': auto,
    }
    return render(request, 'registered/groupmanagement/list.html', context=context)

@login_required
@permission_required('groupmanagement.can_manage_groups')
def group_list_management(request):
    logger.debug("group_list_management called by user %s" % request.user)
    owned = list(request.user.owned_groups.all())
    admin = list(request.user.admin_groups.all())
    auto = AutoGroup.objects.all()
    context = {
        'owned': owned,
        'admin': admin,
        'auto': auto,
    }
    return render(request, 'registered/groupmanagement/list_management.html', context=context)

@login_required
@permission_required('access.site_access')
def group_application_create(request, group_id):
    logger.debug("group_application_create called by user %s for group_id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if GroupApplication.objects.filter(user=request.user).filter(extended_group=exgroup).filter(response=None).exists() is False:
        app = GroupApplication(user=request.user, extended_group=exgroup)
        app.save()
        logger.info("Created %s" % app)
        if app.extended_group.require_application is not True:
            logger.info("Auto-accepting %s as group %s does not require application approval." % (app, app.extended_group))
            app.accept()
    else:
        logger.warn("User %s attempted to duplicate %s" % (request.user, GroupApplication.objects.filter(user=request.user).filter(extended_group=exgroup)[0]))
    return redirect('groupmanagement_group_list')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_application_accept(request, app_id):
    logger.debug("group_application_accept called by user %s for app id %s" % (request.user, app_id))
    app = get_object_or_404(GroupApplication, id=app_id)
    if app.extended_group.owner == request.user or request.user in app.extended_group.admins.all():
        logger.info("User %s accepting %s" % (request.user, app))
        app.accept()
    else:
        logger.warn("User %s not eligible to accept %s" % (request.user, app))
    return redirect('groupmanagement_group_manage', app.extended_group.id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_application_reject(request, app_id):
    logger.debug("group_application_reject called by user %s for app_id %s" % (request.user, app_id))
    app = get_object_or_404(GroupApplication, id=app_id)
    if app.extended_group.owner == request.user or request.user in app.extended_group.admins.all():
        logger.info("User %s rejecting %s" % (request.user, app))
        app.reject()
    else:
        logger.warn("User %s not eligible to reject %s" % (request.user, app))
    return redirect('groupmanagement_group_manage', group_id = app.extended_group.id)

@login_required
@permission_required('access.site_access')
def group_application_delete(request, app_id):
    logger.debug("group_application_delete called by user %s for app_id %s" % (request.user, app_id))
    app = get_object_or_404(GroupApplication, id=app_id)
    if app.user == request.user:
        logger.info("User %s deleting %s" % (request.user, app))
        app.delete()
    else:
        logger.warn("User %s not eligible to delete %s" % (request.user, app))
    return redirect('groupmanagement_group_list')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage.groups')
@permission_required('groupmanagement.add_extendedgroup')
def group_create(request):
    logger.debug("group_create called by user %s" % request.user)
    choices = [(None, 'None'),]
    for g in ExtendedGroup.objects.get_parents_for_user(request.user):
        choices.append((g.id, str(g)))
    if request.method == 'POST':
        form = GroupAddForm(request.POST)
        form.fields['parent'].choices = choices
        logger.debug("Received POST request containing form, is valid: %s" % form.is_valid())
        if form.is_valid():
            name = form.cleaned_data['name']
            desc = form.cleaned_data['description']
            hidden = form.cleaned_data['hidden']
            parent_id = form.cleaned_data['parent']
            if parent_id:
                parent = get_object_or_404(ExtendedGroup, id=parent_id)
            else:
                parent = None
            app = form.cleaned_data['applications']
            group, c = Group.objects.get_or_create(name=name)
            if c is False:
                if ExtendedGroup.objects.filter(group=group).exists() is False:
                    if AutoGroup.obkects.filter(group=group).exists() is False:
                        logger.warn("Associating orphaned group %s with new extended group created by %s" % (group, request.user))
                    else:
                        logger.error("User %s attempting to create ExtendedGroup for %s" % (request.user, AutoGroup.objects.get(group=group)))
                        return redirect('groupmanagement.views.group_list')
                else:
                    logger.error("User %s attempting to create duplicate ExtendedGroup for %s" % (request.user, group))
                    return redirect('groupmanagement.views.group_list')
            e = ExtendedGroup(group=group, owner=request.user, description=desc, hidden=hidden, parent=parent, require_application=app)
            e.save()
            logger.info("User %s created group %s" % (request.user, e))
            return redirect('groupmanagement_group_list_management')
    else:
        form = GroupAddForm()
        form.fields['parent'].choices = choices
    context = {
        'form': form,
        'title': 'Create Group',
        'button_text': 'Create',
    }
    return render(request, 'public/form.html', context=context)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
@permission_required('groupmanagement.delete_extendedgroup')
def group_delete(request, group_id):
    logger.debug("group_delete called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user:
        logger.info("User %s deleting group %s" % (request.user, exgroup))
        exgroup.delete()
    else:
        logger.warn("User %s not eligible to delete group %s" % (request.user, exgroup))
    return redirect('groupmanagement_group_list_management')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_manage(request, group_id):
    logger.debug("group_manage called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user or request.user in exgroup.admins.all():
        members = [(u, exgroup.can_promote_member(request.user, u)) for u in exgroup.basic_members]
        apps = GroupApplication.objects.filter(extended_group=exgroup).filter(response=None)
        admins = [(a, exgroup.can_demote_admin(request.user, a)) for a in exgroup.admins.all()]
        context = {
            'group': exgroup,
            'members': members,
            'admins': admins,
            'applications': apps,
        }
        return render(request, 'registered/groupmanagement/manage.html', context=context)
    else:
        logger.warn("User %s not eligible to manage group %s" % (request.user, exgroup))
        return redirect('groupmanagement_group_list')
    return render(request, 'registered/groupmanagement/manage.html', context=context)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_promote_member(request, group_id, user_id):
    logger.debug("group_promote_member called by user %s for group id %s user id %s" % (request.user, group_id, user_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    member = get_object_or_404(User, pk=user_id)
    if exgroup.can_promote_member(request.user, member):
        if member not in exgroup.admins.all():
            logger.info("User %s promoting %s to group %s admin" % (request.user, member, exgroup))
            exgroup.admins.add(member)
        else:
            logger.warn("User %s cannot promote %s in group %s: already admin" % (request.user, member, exgroup))
    else:
        logger.warn("User %s not eligible to promote %s in group %s" % (request.user, member, exgroup))
    return redirect('groupmanagement_group_manage', group_id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_demote_admin(request, group_id, user_id):
    logger.debug("group_demote_admin called by user %s for group id %s user id %s" % (request.user, group_id, user_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    admin = get_object_or_404(User, pk=user_id)
    if exgroup.owner == request.user or request.user == admin:
        if admin in exgroup.admins.all():
            logger.info("User %s demoting admin %s in group %s" % (request.user, admin, exgroup))
            exgroup.admins.remove(admin)
        else:
            logger.warn("User %s cannot demote %s in group %s: not admin" % (request.user, admin, exgroup))
    else:
        logger.warn("User %s not eligible to demote %s in group %s" % (request.user, admin, exgroup))
    return redirect('groupmanagement_group_manage', group_id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
@permission_required('groupmanagement.change_extendedgroup')
def group_edit(request, group_id):
    logger.debug("group_edit called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user:
        choices = [(None, 'None'),]
        for g in ExtendedGroup.objects.all().exclude(id=exgroup.id).exclude(parent=exgroup):
            logger.debug(g)
            if g.owner == request.user or request.user in g.admins.all():
                choices.append((g.id, str(g)))
        if request.method == 'POST':
            form = GroupEditForm(request.POST)
            form.fields['parent'].choices = choices
            logger.debug("Received POST request containing form, is valid: %s" % form.is_valid())
            if form.is_valid():
                desc = form.cleaned_data['description']
                hidden = form.cleaned_data['hidden']
                app = form.cleaned_data['applications']
                parent_id = form.cleaned_data['parent']
                if parent_id:
                    parent = get_object_or_404(ExtendedGroup, id=parent_id)
                else:
                    parent = None
                update_fields=[]
                if exgroup.description != desc:
                    exgroup.description = desc
                    update_fields.append('description')
                if exgroup.hidden != hidden:
                    exgroup.hidden = hidden
                    update_fields.append('hidden')
                if exgroup.require_application != app:
                    exgroup.require_application = app
                    update_fields.append('require_application')
                if exgroup.parent != parent:
                    exgroup.parent = parent
                    update_fields.append('parent')
                if update_fields:
                    logger.info("User %s updating group %s fields %s" % (request.user, exgroup, update_fields))
                    exgroup.save()
                else:
                    logger.debug("Detected no changes between group %s and supplied form." % exgroup)
                return redirect('groupmanagement_group_list_management')
        else:
            parent = None
            if exgroup.parent:
                parent = exgroup.parent.id
            data = {
                'description': exgroup.description,
                'hidden': exgroup.hidden,
                'parent': parent,
                'applications': exgroup.require_application,
            }
            form = GroupEditForm(initial=data)
            form.fields['parent'].choices = choices
        context = {
            'form': form,
            'title': 'Edit Group',
            'button_text': 'Edit',
        }
        return render(request, 'public/form.html', context=context)
    else:
        logger.warn("User %s not eligible to edit group %s" % (request.user, exgroup))
        return redirect('groupmanagement_group_list_management')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
@permission_required('groupmanagement.change_extendedgroup')
def group_transfer_ownership(request, group_id):
    logger.debug("group_transfer_ownership called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    choices = []
    for a in exgroup.admins.all():
        choices.append((a.pk, str(a)))
    if exgroup.owner == request.user:
        if request.method == 'POST':
            form = GroupTransferForm(request.POST)
            form.fields['owner'].choices = choices
            logger.debug("Request type POST, contains for, is valid: %s" % form.is_valid())
            if form.is_valid():
                admin_id = form.cleaned_data['owner']
                admin = get_object_or_404(User, pk=admin_id)
                exgroup.owner = admin
                logger.info("User %s transferring ownership of group %s to %s" % (request.user, exgroup, admin))
                exgroup.save(update_fields=['owner'])
                return redirect('groupmanagement_group_list_management')
        else:
            form = GroupTransferForm()
            form.fields['owner'].choices = choices
            if not exgroup.admins.all():
                logger.warn("User %s unable to transfer ownership of %s - no admins found." % (request.user, exgroup))
                return redirect('groupmanagement_group_list_management')
        context = {
            'form': form,
            'title': 'Transfer Ownership of %s' % exgroup,
            'button_text': 'Transfer',
        }
        return render(request, 'public/form.html', context=context)
    else:
        logger.warn("User %s not eligible to transfer ownership of %s" % (request.user, exgroup))
        return redirect('groupmanagement_group_manage', group_id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_remove_member(request, group_id, user_id):
    logger.debug("group_remove_member called by user %s for group id %s user id %s" % (request.user, group_id, user_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    member = get_object_or_404(User, pk=user_id)
    if exgroup.can_remove_member(request.user, member):
        if exgroup.group in member.groups.all():
            if member != exgroup.owner and member not in exgroup.admins.all():
                logger.info("User %s removing member %s from group %s" % (request.user, member, exgroup))
                member.groups.remove(exgroup.group)
            else:
                logger.warn("User %s failed to remove member %s from group %s - member is management." % (request.user, member, exgroup))
        else:
            logger.warn("User %s failed to remove member %s from group %s - member not in group." % (request.user, member, exgroup))
    else:
        logger.warn("User %s not eligible to remove member %s from group %s" % (request.user, member, exgroup))
    return redirect('groupmanagement_group_manage', group_id)

@login_required
@permission_required('access.site_access')
def group_leave(request, group_id):
    logger.debug("group_leave called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.can_leave_group(request.user):
        if exgroup.group in request.user.groups.all():
            logger.info("User %s leaving group %s" % (request.user, exgroup))
            request.user.groups.remove(exgroup.group)
        else:
            logger.warn("User %s unable to leave group %s - not a member." % (request.user, exgroup))
    else:
        logger.warn("User %s unable to leave group %s - is management." % (request.user, exgroup))
    return redirect('groupmanagement_group_list')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.add_autogroup')
def auto_group_add(request):
    logger.debug("auto_group_add called by user %s" % request.user)
    choices = []
    for aa in AllianceAccessRule.objects.all():
        if not aa.auto_group.exists():
            choices.append(('alliance %s' % aa.pk, aa))
    for ca in CorpAccessRule.objects.all():
        if not ca.auto_group.exists():
            choices.append(('corp %s' % ca.pk, ca))
    for ca in CharacterAccessRule.objects.all():
        if not ca.auto_group.exists():
            choices.append(('character %s' % ca.pk, ca))
    logger.debug(choices)
    if request.method == 'POST':
        form = AutoGroupForm(request.POST)
        form.fields['access_rule'].choices = choices
        if form.is_valid():
            name = form.cleaned_data['name']
            group, c = Group.objects.get_or_create(name=name)
            if not c:
                form.add_error(None, 'Somehow that group already exists. Pick a different name')
            else:
                access_str = str.split(str(form.cleaned_data['access_rule']))
                type = access_str[0]
                id = access_str[1]
                rule = None
                if type == "alliance":
                    rule = get_object_or_404(AllianceAccessRule, pk=id)
                elif type == "corp":
                    rule = get_object_or_404(CorpAccessRule, pk=id)
                elif type == "character":
                    rule = get_object_or_404(CharacterAccessRule, pk=id)
                else:
                    form.add_error(None, 'Unknown access rule type.')
                if rule:
                    ag = AutoGroup(group=group)
                    ag.set_rule(rule)
                    logger.info("User %s creating %s" % (request.user, ag))
                    ag.save()
                    return redirect('groupmanagement_group_list_management')
    else:
        form = AutoGroupForm()
        form.fields['access_rule'].choices = choices
    context = {
        'form': form,
        'title': 'Create Auto Group',
        'button_text': 'Create',
    }
    return render(request, 'public/form.html', context=context)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.delete_autogroup')
def auto_group_delete(request, ag_id):
    logger.debug("auto_group_delete called by user %s for ag_id %s" % (request.user, ag_id))
    ag = get_object_or_404(AutoGroup, pk=ag_id)
    logger.info("User %s deleting %s" % (request.user, ag))
    ag.delete()
    return redirect('groupmanagement_group_list_management')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def auto_group_view(request, ag_id):
    logger.debug("auto_group_view called by user %s for ag_id %s" % (request.user, ag_id))
    ag = get_object_or_404(AutoGroup, pk=ag_id)
    users = ag.group.user_set.all()
    return render(request, 'registered/groupmanagement/group_member_list.html', context={'group': ag, 'users': users})
