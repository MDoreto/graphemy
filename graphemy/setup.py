import os

from dotenv import load_dotenv
from strawberry.permission import BasePermission

load_dotenv()


class Setup:
    engine = None
    folder = os.getenv('GRAPHEMY_PATH')
    get_permission = None

    @classmethod
    def setup(cls, engine, get_perm=None):
        cls.engine = engine

        def get_permission(module, context):
            return True

        if get_perm:
            cls.get_permission = get_perm
        else:
            cls.get_permission = get_permission

    @classmethod
    def get_auth(cls, module):
        class IsAuthenticated(BasePermission):
            def has_permission(self, source, info, **kwargs) -> bool:
                if not cls.get_permission(module, info):
                    info.context['response'].status_code = 403
                    if not 'errors' in info.context['request'].scope:
                        info.context['request'].scope['errors'] = [module]
                    elif not module in info.context['request'].scope['errors']:
                        info.context['request'].scope['errors'].append(module)
                return True

        return IsAuthenticated
