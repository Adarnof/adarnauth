from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User, Group
from .forms import GroupAddForm, GroupEditForm, GroupTransferForm
from .models import GroupApplication, ExtendedGroup
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test

@login_required
@permission_required('useraccess.site_access')
def group_list(request):
    logger.debug("group_list_view called by user %s" % request.user)
    applications = GroupApplication.objects.get_open.filter(user=request.user)
    applied = [a.extended_group for a in applications]
    owned = user.owned_groups.all()
    admin = user.admin_groups.all()
    user_groups = ExtendedGroup.objecs.filter(group in request.user.groups.all())
    all_groups = ExtendedGroup.objects.all() - user_groups - applied
    for g in all_groups:
        if g.hidden:
            all_groups.remove(g)
        elif not g.parent in user_groups:
            all_groups.remove(g)
    for g in owned:
        user_groups.remove(g)
    for g in admin:
        user_groups.remove(g)
    logger.debug("Collected %s owned %s admin %s member %s available %s applied groups for user %s" % (len(owned), len(admin), len(user_groups), len(all_groups), len(applied), request.user))
    context = {
        'owned': owned,
        'admin': admin,
        'member': user_groups,
        'available': all_groups,
    }
    return render(request, 'registered/groupmanagement/list.html', context=context)

@login_required
@permission_required('access.site_access')
def group_application_create(request, group_id):
    logger.debug("group_application_create called by user %s for group_id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if not GroupApplication.objects.filter(user=request.user).filter(extended_group=exgroup).exists():
        app = GroupApplication(user=request.user, extended_group=exgroup)
        app.save()
        logger.info("Created %s" % app)
    else:
        logger.warn("User %s attempted to duplicate %s" % (request.user, GroupApplication.objects.filter(user=request.user).filter(extended_group=exgroup)[0]))
    return redirect('groupmanagement.views.group_list_view')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_application_accept(request, app_id):
    logger.debug("group_application_accept called by user %s for app id %s" % (request.user, group_id))
    app = get_object_or_404(GroupApplication, id=app_id)
    if app.extended_group.owner == request.user or request.user in app.extended_group.admins:
        logger.info("User %s accepting %s" % (request.user, app))
        app.accept()
    else:
        logger.warn("User %s not eligible to accept %s" % (request.user, app))
    return redirect('groupmanagement.views.group_manage', group_id = app.extended_group.id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_groups')
def group_application_reject(request, app_id):
    logger.debug("group_application_reject called by user %s for app_id %s" % (request.user, group_id))
    app = get_object_or_404(GroupApplication, id=app_id)
    if app.extended_group.owner == request.user or request.user in app.extended_group.admins:
        logger.info("User %s rejecting %s" % (request.user, app))
        app.reject()
    else:
        logger.warn("User %s not eligible to reject %s" % (request.user, app))
    return redirect('groupmanagement.views.group_manage', group_id = app.extended_group.id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage.groups')
@permission_required('groupmanagement.add_extendedgroup')
def group_create(request):
    logger.debug("group_create called by user %s")
    if request.method == 'POST':
        form = GroupAddForm(request.POST)
        logger.debug("Received POST request containing form, is valid: %s" % form.is_valid())
        if form.is_valid():
            name = form.cleaned_data['name']
            desc = form.cleaned_data['description']
            hidden = form.cleaned_data['hidden']
            parent_str = form.cleaned_data['parent']
            app = form.cleaned_data['applications']
            if parent_str:
                parent = get_object_or_404(ExtendedGroup, name=parent_str)
            else:
                parent = None
            logger.debug("Proceeding with creation of group %s with parent: %s" % (name, parent))
            group, c = Group.objects.get_or_create(name=name)
            if not c:
                logger.warn("Associating orphaned group %s with new extended group created by %s" % (group, request.user))
            e = ExtendedGroup(group=group, owner=request.user, description=desc, hidden=hidden, parent=parent, require_application=app)
            e.save()
            logger.info("User %s created group %s" % (request.user, e))
    else:
        form = GroupAddForm()
    return render(request, 'registered/groupmanagemement/create.html', context={'form':form})

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
@permission_required('groupmanagement.delete_extendedgroup')
def group_delete(request, group_id):
    logger.debug("group_delete called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user:
        logger.info("User %s deleting group %s" % (request.user, exgroup))
        exgroup.delete()
    else:
        logger.warn("User %s not eligible to delete group %s" % (request.user, exgroup))
    return redirect('groupmanagement.views.group_list')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
def group_manage(request, group_id):
    logger.debug("group_manage called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user or request.user in exgroup.admins.all():
        all_users = exgroup.group.user_set.all() - [exgroup.owner] - exgroup.admins.all()
        members = []
        for u in all_users:
            can_admin = False
            if u.has_perm('groupmanagement.can_manage_group') and request.user == exgroup.owner:
                can_admin = True
            members.append((u, can_admin))
        apps = GroupApplication.objects.filter(group=exgroup)
        context = {
            'group': exgroup,
            'members': members,
            'applications': apps,
        }
        return render(request, 'registered/groupmanagement/manage.html', context=context)
    else:
        logger.warn("User %s not eligible to manage group %s" % (request.user, exgroup))
    return render(request, 'registered/groupmanagement/manage.html', context=context)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
def group_promote_member(request, group_id, user_id):
    logger.debug("group_promote_member called by user %s for group id %s user id %s" % (request.user, group_id, user_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    member = get_object_or_404(User, pk=user_id)
    if exgroup.owner == request.user:
        if not member in exgroup.admins.all():
            logger.info("User %s promoting %s to group %s admin" % (request.user, member, exgroup))
            exgroup.admins.add(member)
        else:
            logger.warn("User %s cannot promote %s in group %s: already admin" % (request.user, member, exgroup))
    else:
        logger.warn("User %s not eligible to promote %s in group %s" % (request.user, member, exgroup))
    return redirect('groupmanagement.views.group_manage', group_id=group_id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
def group_demote_admin(request, group_id, user_id):
    logger.debug("group_demote_admin called by user %s for group id %s user id %s" % (request.user, group_id, user_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    admin = get_object_or_404(User, id=user_id)
    if exgroup.owner == request.user:
        if admin in exgroup.admins.all():
            logger.info("User %s demoting admin %s in group %s" % (request.user, admin, exgroup))
        else:
            logger.warn("User %s cannot demote %s in group %s: not admin" % (request.user, admin, exgroup))
    else:
        logger.warn("User %s not eligible to demote %s in group %s" % (request.user, admin, exgroup))
    return redirect('groupmanagement.views.group_manage', group_id=group_id)

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
@permission_required('groupmanagement.change_extendedgroup')
def group_edit(request, group_id):
    logger.debug("group_edit called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user:
        if request.method == 'POST':
            form = GroupEditForm(request.POST)
            logger.debug("Received POST request containing form, is valid: %s" % form.is_valid())
            if form.is_valid():
                desc = form.cleaned_data['desc']
                hidden = form.cleaned_data['hidden']
                app = form.cleaned_data['applications']
                parent_str = form.cleaned_data['parent']
                if parent_str:
                    parent = get_object_or_404(ExtendedGroup, name=parent_str)
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
        else:
            form = GroupEditForm()
        return render(request, 'registered/groupmanagement/edit.html', context={'form':form})
    else:
        logger.warn("User %s not eligible to edit group %s" % (request.user, exgroup))
        return redirect('groupmanagement.views.group_list')

@login_required
@permission_required('access.site_access')
@permission_required('groupmanagement.can_manage_group')
@permission_required('groupmanagement.change_extendedgroup')
def group_transfer_ownership(request, group_id):
    logger.debug("group_transfer_ownership called by user %s for group id %s" % (request.user, group_id))
    exgroup = get_object_or_404(ExtendedGroup, id=group_id)
    if exgroup.owner == request.user:
        if request.method == 'POST':
            form = GroupTransferForm(request.POST)
            logger.debug("Request type POST, contains for, is valid: %s" % form.is_valid())
            if form.is_valid():
                admin_id = int(form.cleaned_data['owner'])        
                admin = get_object_or_404(User, pk=admin_id)
                exgroup.owner = admin
                logger.info("User %s transferring ownership of group %s to %s" % (request.user, exgroup, admin))
                exgroup.save(update_fields=['owner'])
        else:
            form = GroupTransferForm()
        return render(request, 'registered/groupmanagement/transfer.html', context={'form':form})
    else:
        logger.warn("User %s not eligible to transfer ownership of %s" % (request.user, exgroup))
        return redirect('groupmanagement.views.group_manage', group_id=group_id)
