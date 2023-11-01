from strawberry.permission import BasePermission


class Setup:
    engine = None
    folder = ''

    @classmethod
    def setup(cls, engine, folder):
        print('setting', engine)
        cls.engine = engine
        cls.folder = folder

    def get_permission(module, info):
        return True

    @classmethod
    def get_auth(cls, module):
        class IsAuthenticated(BasePermission):
            async def has_permission(self, source, info, **kwargs) -> bool:
                return cls.get_permission(module, info)

        return IsAuthenticated
