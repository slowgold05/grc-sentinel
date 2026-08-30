from sqlalchemy import create_engine

from ruleset.config import settings

engine = create_engine(str(settings.database_url), pool_pre_ping=True)
