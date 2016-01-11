from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import Group
from authentication.models import User
from .forms import GroupAddForm, GroupEditForm, GroupTransferForm
from .models import GroupApplication, ExtendedGroup
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
import logging

logger = logging.getLogger(__name__)

@login_required
@permission_required('useraccess.site_access')
def group_list(request):
    logger.debug("group_list_view called by user %s" % request.user)
    applications = GroupApplication.objects.get_open().filter(user=request.user)
    applied = [a.extended_group for a in applications]
    owned = list(request.user.owned_groups.all())
    admin = list(request.user.admin_groups.all())
    user_groups = []
    for g in request.user.groups.all():
        if ExtendedGroup.objects.filter(group=g).exists():
            user_groups.append(ExtendedGroup.objects.get(group=g))
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
    }
    return render(request, 'registered/groupmanagement/list.html', context=context)

@login_required
@permission_required('groupmanagement.can_manage_groups')
def group_list_management(request):
    logger.debug("group_list_management called by user %s" % request.user)
    owned = list(request.user.owned_groups.all())
    admin = list(request.user.admin_groups.all())
    context = {
        'owned': owned,
        'admin': admin,
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
    logger.debug("group_application_accept called by user %s for app id %s" % (request.user, group_id))
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
    logger.debug("group_application_reject called by user %s for app_id %s" % (request.user, group_id))
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
    for g in ExtendedGroup.objects.all():
        if g.owner == request.user or request.user in g.admins.all():
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
                    logger.warn("Associating orphaned group %s with new extended group created by %s" % (group, request.user))
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
    return render(request, 'registered/groupmanagement/create.html', context={'form':form})

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
        all_users = list(u for u in exgroup.group.user_set.all() if u != exgroup.owner and u not in list(exgroup.admins.all()))
        members = []
        for u in all_users:
            can_admin = False
            if u.has_perm('groupmanagement.can_manage_groups') and request.user == exgroup.owner:
                can_admin = True
            members.append((u, can_admin))
        apps = GroupApplication.objects.filter(extended_group=exgroup).filter(response=None)
        all_admins = list(exgroup.admins.all())
        admins = []
        for a in all_admins:
            if request.user == exgroup.owner:
                admins.append((a, True))
            elif request.user == a:
                admins.append((a, True))
            else:
                admins.append((a, False))
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
    if exgroup.owner == request.user:
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
            data = {
                'description': exgroup.description,
                'hidden': exgroup.hidden,
                'parent': exgroup.parent,
                'applications': exgroup.require_application,
            }
            form = GroupEditForm(initial=data)
            form.fields['parent'].choices = choices
        return render(request, 'registered/groupmanagement/edit.html', context={'form':form})
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
        return render(request, 'registered/groupmanagement/transfer.html', context={'form':form})
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
    if exgroup.owner == request.user or request.user in exgroup.admins.all():
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
    if exgroup.owner != request.user and request.user not in exgroup.admins.all():
        if exgroup.group in request.user.groups.all():
            logger.info("User %s leaving group %s" % (request.user, exgroup))
            request.user.groups.remove(exgroup.group)
        else:
            logger.warn("User %s unable to leave group %s - not a member." % (request.user, exgroup))
    else:
        logger.warn("User %s unable to leave group %s - is management." % (request.user, exgroup))
    return redirect('groupmanagement_group_list')
