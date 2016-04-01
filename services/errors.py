class ServiceError(Exception):
    def __init__(self, msg, service):
        self.service = service
        self.msg = msg
    def __str__(self):
        return str(self.service) + ': ' + str(self.msg)

class ServiceUnreachableError(ServiceError):
    def __init__(self, msg, service, source_error):
        super(ServiceUnreachableError, self).__init__(msg, service)
        self.source_error = source_error
    def __str__(self):
        return super(ServiceUnreachableError, self).__str__() + '\nSource: ' + str(self.source_error)

class RequiredGroupsError(ServiceError):
    def __init__(self, msg, service, user):
        super(RequiredGroupsError, self).__init__(msg, service)
        self.user = user
    def __str__(self):
        return super(RequiredGroupsError, self).__str__() + '\nUser: ' + str(user.groups.all()) + '\nRequired: ' + str(self.service.required_groups.all())

class UserNotActiveError(ServiceError):
    def __init__(self, msg, service, user):
        super(RequiredGroupsError, self).__init__(msg, service)
        self.user = user
    def __str__(self):
        return super(UserNotActiveError, self).__str__() + '\nUser: ' + str(self.user)

class DuplicateGroupError(ServiceError):
    def __init__(self, msg, group_name):
        super(RequiredGroupsError, self).__init__(msg, service)
        self.group_name = group_name
    def __str__(self):
        return super(DuplicateGroupError, self).__str__() + '\nGroup Name: ' + str(self.group_name)
