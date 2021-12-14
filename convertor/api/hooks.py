from pecan import hooks

from convertor.common import context


class ContextHook(hooks.PecanHook):
    """Configures a request context and attaches it to the request.
    The following HTTP request headers are used:
    X-User:
        Used for context.user.
    X-User-Id:
        Used for context.user_id.
    X-Project-Name:
        Used for context.project.
    X-Project-Id:
        Used for context.project_id.
    X-Auth-Token:
        Used for context.auth_token.
    """

    def before(self, state):
        headers = state.request.headers
        user = headers.get('X-User')
        user_id = headers.get('X-User-Id')
        project = headers.get('X-Project-Name')
        project_id = headers.get('X-Project-Id')
        domain_id = headers.get('X-User-Domain-Id')
        domain_name = headers.get('X-User-Domain-Name')
        auth_token = headers.get('X-Storage-Token')
        auth_token = headers.get('X-Auth-Token', auth_token)
        show_deleted = headers.get('X-Show-Deleted')
        auth_token_info = state.request.environ.get('keystone.token_info')
        roles = (headers.get('X-Roles', None) and
                 headers.get('X-Roles').split(','))

        state.request.context = context.make_context(
            auth_token=auth_token,
            auth_token_info=auth_token_info,
            user=user,
            user_id=user_id,
            project=project,
            project_id=project_id,
            domain_id=domain_id,
            domain_name=domain_name,
            show_deleted=show_deleted,
            roles=roles)
