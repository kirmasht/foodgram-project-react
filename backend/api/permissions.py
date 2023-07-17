from rest_framework.permissions import IsAuthenticatedOrReadOnly


class AuthorStaffOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return (request.method == 'GET'
                or (request.user == obj.author)
                or request.user.is_staff)
