import sys, re, inspect, operator
import logging
from util import emit, name2label, plural, singular
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
try:
    from sqlalchemy.ext.declarative import _deferred_relationship
except ImportError:
    #SA 0.5 support
    from sqlalchemy.ext.declarative import _deferred_relation as _deferred_relationship
    
from sqlalchemy.orm import relation, backref, class_mapper, Mapper

try:
    from sqlalchemy.orm import RelationshipProperty
except ImportError:
    #SA 0.5 support
    from sqlalchemy.orm import RelationProperty as RelationshipProperty


import config
import constants
from formatter import _repr_coltype_as

log = logging.getLogger('saac.decl')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)

def by_name(a, b):
    if a.name>b.name:
        return 1
    return -1
def by__name__(a, b):
    if a.__name__ > b.__name__:
        return 1
    return -1

def column_repr(self):

    kwarg = []
    if self.key != self.name:
        kwarg.append( 'key')

    if hasattr(self, 'primary_key') and self.primary_key:
        self.primary_key = True
        kwarg.append( 'primary_key')

    if not self.nullable:
        kwarg.append( 'nullable')
    if self.onupdate:
        kwarg.append( 'onupdate')
    if self.default:
        kwarg.append( 'default')
    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg)

    name = self.name

    if not hasattr(config, 'options') and config.options.generictypes:
        coltype = repr(self.type)
    elif type(self.type).__module__ == 'sqlalchemy.types':
        coltype = repr(self.type)
    else:
        # Try to 'cast' this column type to a cross-platform type
        # from sqlalchemy.types, dropping any database-specific type
        # arguments.
        for base in type(self.type).__mro__:
            if (base.__module__ == 'sqlalchemy.types' and
                base.__name__ in sqlalchemy.__all__):
                coltype = _repr_coltype_as(self.type, base)
                break
        # FIXME: if a dialect has a non-standard type that does not
        # derive from an ANSI type, there's no choice but to ignore
        # generic-types and output the exact type. However, import
        # headers have already been output and lack the required
        # dialect import.
        else:
            coltype = repr(self.type)

    data = {'name': self.name,
            'type': coltype,
            'constraints': ', '.join(["ForeignKey('%s')"%cn.target_fullname for cn in self.foreign_keys]),
            'args': ks and ks or '',
            }

    if data['constraints']:
        if data['constraints']: data['constraints'] = ', ' + data['constraints']
    if data['args']:
        if data['args']: data['args'] = ', ' + data['args']

    return constants.COLUMN % data

class ModelFactory(object):

    def __init__(self, config):
        self.config = config
        self.used_model_names = []
        self.used_table_names = []
        schema = getattr(self.config, 'schema', None)
        self._metadata = MetaData(bind=config.engine)
        kw = {}
        self.schemas = None
        if schema:
            if isinstance(schema, (list, tuple)):
                self.schemas = schema
            else:
                self.schemas = (schema, )
            for schema in self.schemas:
                log.info('Reflecting database... schema:%s'%schema)
                self._metadata.reflect(schema=schema)
        else:
            log.info('Reflecting database...')
            self._metadata.reflect()

        self.DeclarativeBase = declarative_base(metadata=self._metadata)

    def _table_repr(self, table):
        s = "Table(u'%s', metadata,\n"%(table.name)
        for column in table.c:
            s += "    %s,\n"%column_repr(column)
        if table.schema:
            s +="    schema='%s'\n"%table.schema
        s+=")"
        return s

    def __repr__(self):
        tables = self.get_many_to_many_tables()
        models = self.models


        s = StringIO()
        engine = self.config.engine
        if not isinstance(engine, basestring):
            engine = str(engine.url)
        s.write(constants.HEADER_DECL%engine)
        if 'postgres' in engine:
            s.write(constants.PG_IMPORT)

        self.used_table_names = []
        self.used_model_names = []
        for table in tables:
            table_name = self.find_new_name(table.name, self.used_table_names)
            self.used_table_names.append(table_name)
            s.write('%s = %s\n\n'%(table_name, self._table_repr(table)))

        for model in models:
            s.write(model.__repr__())
            s.write("\n\n")

        if self.config.example or self.config.interactive:
            s.write(constants.EXAMPLE_DECL%(models[0].__name__,models[0].__name__))
        if self.config.interactive:
            s.write(constants.INTERACTIVE%([model.__name__ for model in models], models[0].__name__))
        return s.getvalue()

    @property
    def tables(self):
        return self._metadata.tables.keys()

    @property
    def models(self):
        self.used_model_names = []
        self.used_table_names = []
        return sorted((self.create_model(table) for table in self.get_non_many_to_many_tables()), by__name__)

    def find_new_name(self, prefix, used, i=0):
        if i!=0:
            prefix = "%s%d"%(prefix, i)
        if prefix in used:
            prefix = prefix
            return self.find_new_name(prefix, used, i+1)
        return prefix


    def create_model(self, table):
        #partially borrowed from Jorge Vargas' code
        #http://dpaste.org/V6YS/
        log.debug('Creating Model from table: %s'%table.name)

        model_name = self.find_new_name(singular(name2label(table.name)), self.used_model_names)
        self.used_model_names.append(model_name)
        is_many_to_many_table = self.is_many_to_many_table(table)
        table_name = self.find_new_name(table.name, self.used_table_names)
        self.used_table_names.append(table_name)


        class Temporal(self.DeclarativeBase):
            __table__ = table

            @classmethod
            def _relation_repr(cls, rel):
                target = rel.argument
                if target and inspect.isfunction(target):
                    target = target()
                if isinstance(target, Mapper):
                    target = target.class_
                target = target.__name__
                secondary = ''
                if rel.secondary is not None:
                    secondary = ", secondary=%s"%rel.secondary.name
                backref=''
#                if rel.backref:
#                    backref=", backref='%s'"%rel.backref.key
                return "%s = relation('%s'%s%s)"%(rel.key, target, secondary, backref)

            @classmethod
            def __repr__(cls):
                log.debug('repring class with name %s'%cls.__name__)
                try:
                    mapper = class_mapper(cls)
                    s = ""
                    s += "class "+model_name+'(DeclarativeBase):\n'
                    if is_many_to_many_table:
                        s += "    __table__ = %s\n\n"%table_name
                    else:
                        s += "    __tablename__ = '%s'\n\n"%table_name
                        if hasattr(cls, '__table_args__'):
                            s+="    __table_args__ = %s"%cls.__table_args__
                        s += "    #column definitions\n"
                        for column in sorted(cls.__table__.c, by_name):
                            s += "    %s = %s\n"%(column.name, column_repr(column))
                    s += "\n    #relation definitions\n"
                    ess = s
                    for prop in mapper.iterate_properties:
                        if isinstance(prop, RelationshipProperty):
                            s+='    %s\n'%cls._relation_repr(prop)
                    return s
                except Exception, e:
                    log.error("Could not generate class for: %s"%cls.__name__)
                    from traceback import format_exc
                    log.error(format_exc())
                    return ''
                    

        #hack the class to have the right classname
        Temporal.__name__ = model_name

        #add in the schema
        if self.config.schema:
            Temporal.__table_args__ = {'schema':table.schema}

        #trick sa's model registry to think the model is the correct name
        if model_name != 'Temporal':
            Temporal._decl_class_registry[model_name] = Temporal._decl_class_registry['Temporal']
            del Temporal._decl_class_registry['Temporal']

        
        #add in single relations
        fks = self.get_foreign_keys(table)
        for related_table in sorted(fks.keys(), by_name):
            columns = fks[related_table]
            if len(columns)>1:
                continue
            column = columns[0]
            log.info('    Adding <primary> foreign key for:%s'%related_table.name)
            backref_name = plural(table_name)
#            import ipdb; ipdb.set_trace()
            rel = relation(singular(name2label(related_table.name, related_table.schema)), primaryjoin=column==column.foreign_keys[0].column)#, backref=backref_name)
            setattr(Temporal, related_table.name, _deferred_relationship(Temporal, rel))
        
        """
        #add in many-to-many relations
        for join_table in self.get_related_many_to_many_tables(table.name):
            for column in join_table.columns:
                if column.foreign_keys:
                    key = column.foreign_keys[0]
                    if key.column.table is not table:
                        related_table = column.foreign_keys[0].column.table
                        log.info('    Adding <secondary> foreign key(%s) for:%s'%(key, related_table.name))
                        import ipdb; ipdb.set_trace()
                        setattr(Temporal, plural(related_table.name), _deferred_relationship(Temporal,
                                                                                         relation(singular(name2label(related_table.name,
                                                                                                             related_table.schema)),
                                                                                                  secondary=join_table
                                                                                                  secondaryjoin=
                                                                                                  
                                                                                                  )))
                        break;
        """
        return Temporal

    def get_table(self, name):
        """(name) -> sqlalchemy.schema.Table
        get the table definition with the given table name
        """
        if self.schemas:
            for schema in self.schemas:
                if schema and not name.startswith(schema):
                    new_name = '.'.join((schema, name))
                table = self._metadata.tables.get(new_name, None)
                if table is not None:
                    return table
        return self._metadata.tables[name]

    def get_foreign_keys(self, table):
        fks = {}
        for column in table.columns:
            if len(column.foreign_keys)>0:
                fks.setdefault(column.foreign_keys[0].column.table, []).append(column)
        return fks

    def is_many_to_many_table(self, table):
        fks = self.get_foreign_keys(table).values()
        if len(fks) >= 2:
            if len(fks[0]) == 1 and len(fks[1]) == 1:
                return fks[0][0].foreign_keys[0].column.table != fks[1][0].foreign_keys[0].column.table
        return False

    def is_only_many_to_many_table(self, table):
        return len(self.get_foreign_keys(table)) == 2 and len(table.c) == 2

    def get_many_to_many_tables(self):
        if not hasattr(self, '_many_to_many_tables'):
            self._many_to_many_tables = [table for table in self._metadata.tables.values() if self.is_many_to_many_table(table)]
        return sorted(self._many_to_many_tables, by_name)

    def get_non_many_to_many_tables(self):
        tables = [table for table in self._metadata.tables.values() if not(self.is_only_many_to_many_table(table))]
        return sorted(tables, by_name)

    def get_related_many_to_many_tables(self, table_name):
        tables = []
        src_table = self.get_table(table_name)
        for table in self.get_many_to_many_tables():
            for column in table.columns:
                if column.foreign_keys:
                    key = column.foreign_keys[0]
                    if key.column.table is src_table:
                        tables.append(table)
                        break
        return sorted(tables, by_name)
