from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from strawberry.permission import BasePermission


class Setup:
    engine = None
    folder = ''
    get_permission = None
    async_engine = False

    @classmethod
    async def execute_query(cls, query):
        if cls.async_engine:
            async_session = sessionmaker(
                cls.engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                r = await session.execute(query)
                return r.scalars().all()
        else:
            with Session(cls.engine) as session:
                r = session.exec(query).all()

    @classmethod
    def setup(cls, engine, folder=None, get_perm=None, query_filter=True):
        if engine and 'async' in engine.__module__:
            cls.async_engine = True
        cls.engine = engine
        if query_filter:
            cls.query_filter = query_filter
        else:
            def query_filter_default(cls,info):
                return True
            cls.query_filter = query_filter_default
            
        if folder:
            cls.folder = folder
        if get_perm:
            cls.get_permission = get_perm
        else:

            async def get_permission(module_class, context):
                return True

            cls.get_permission = get_permission

    @classmethod
    def get_auth(cls, module, request_type):
        class IsAuthenticated(BasePermission):
            async def has_permission(self, source, info, **kwargs) -> bool:
                if not await module.permission_getter(
                    info
                ) or not await cls.get_permission(
                    module, info.context, request_type
                ):
                    info.context['response'].status_code = 403
                    if not 'errors' in info.context['request'].scope:
                        info.context['request'].scope['errors'] = [module]
                    elif not module in info.context['request'].scope['errors']:
                        info.context['request'].scope['errors'].append(module)
                return True

        return IsAuthenticated
