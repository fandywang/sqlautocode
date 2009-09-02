import os
from nose.tools import eq_
from sqlautocode.declarative import ModelFactory
from sqlalchemy.orm import class_mapper
testdb = os.path.abspath(os.path.dirname(__file__))+'/data/devdata.db'

print testdb
class DummyConfig:
    engine = 'sqlite:///'+testdb

class TestModelFactory:
    
    def setup(self):
        self.config = DummyConfig()
        self.factory = ModelFactory(self.config)
    
    def test_tables(self):
        tables = sorted(self.factory.tables)
        eq_(tables,  [u'tg_group', u'tg_group_permission', u'tg_permission', u'tg_town', u'tg_user', u'tg_user_group'])

    def _setup_all_models(self):
        return self.factory.models

    def test_create_model(self):
        Group      = self.factory.create_model(self.factory._metadata.tables['tg_group'])
        Permission = self.factory.create_model(self.factory._metadata.tables['tg_permission'])
        Town       = self.factory.create_model(self.factory._metadata.tables['tg_town'])
        User       = self.factory.create_model(self.factory._metadata.tables['tg_user'])

        class_mapper(Town)
        class_mapper(User)
        
        t = Town(town_name="Arvada")
        u = User(tg_town=t)
        assert u.tg_town.town_name == 'Arvada'
        
    def test_get_many_to_many_tables(self):
        tables = sorted([table.name for table in self.factory.get_many_to_many_tables()])
        eq_(tables, [u'tg_group_permission', u'tg_user_group'])
    
    def test_get_related_many_to_many_tables(self):
        tables = [table.name for table in self.factory.get_related_many_to_many_tables('tg_user')]
        eq_(tables, [u'tg_user_group'])
        
    def test_get_foreign_keys(self):
        columns = [column.name for column in sorted(self.factory.get_foreign_keys(self.factory._metadata.tables['tg_user']))]
        eq_(columns, ['town_id'])
        
        
    def test_model__repr__(self):
        models = sorted(self._setup_all_models())
        for model in models:
            if model.__name__=='TgUser':
                User = model
        r = User.__repr__()
        expected = """class TgUser(DeclarativeBase):
    __table_name__ = 'tg_user'

    #column definitions
    user_id = Column(u'user_id', Integer(), primary_key=1, nullable=False)
    user_name = Column(u'user_name', String(length=16, convert_unicode=False, assert_unicode=None), primary_key=0, nullable=False)
    email_address = Column(u'email_address', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=0, nullable=False)
    display_name = Column(u'display_name', String(length=255, convert_unicode=False, assert_unicode=None), primary_key=0)
    town_id = Column(u'town_id', Integer(), primary_key=0)
    password = Column(u'password', String(length=80, convert_unicode=False, assert_unicode=None), primary_key=0)
    created = Column(u'created', DateTime(timezone=False), primary_key=0)

    #relation definitions
    tg_town = relation(TgTown, backref='tg_users')
    tg_groups = relation(TgGroup, secondary=tg_user_group)
"""
        eq_(r.strip(), expected.strip())
    
    def test__repr__(self):
        
        r = repr(self.factory)
        print r
        expected = """"""
        eq_(r.strip(), expected.strip())