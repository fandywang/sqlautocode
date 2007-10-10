
from sqlalchemy import *
import constants

def textclause_repr( self):
    return 'text(%r)' % self.text

def table_repr( self):

    data = {'name' : self.name,
            'columns' : constants.NLTAB.join([repr(cl) for cl in self.columns]),
            'constraints' : constants.NLTAB.join([repr(cn) for cn in self.constraints 
                                        if not isinstance(cn, PrimaryKeyConstraint)]),
            'index' : '',
            'schema' : self.schema != None and "schema='%s'" % self.schema or ''}
    
    # if index data should be included is defined by a property
    # on the table object set by autocode (__indexdata__)
    if hasattr(self, '__indexdata__'):
        data['index'] = getattr(self, '__indexdata__')

        if data['constraints']:
            data['constraints'] = data['constraints'] + ','

        return constants.TABLE % data

    else:
        if data['constraints']:
            data['constraints'] = data['constraints'] + ','

    return constants.TABLE_WO_INDEX % data

def column_repr( self):
    kwarg = []
    if self.key != self.name: kwarg.append( 'key')
    if self._primary_key: kwarg.append( 'primary_key')
    if not self.nullable: kwarg.append( 'nullable')
    if self.onupdate: kwarg.append( 'onupdate')
    if self.default: kwarg.append( 'default')
    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg )
        
    name = self.name
    type = self.type

    data = {'name' : self.name, 
            'type' : self.type,
            'constraints' : ', '.join([repr(cn) for cn in self.constraints]),
            'args' : ks and ks or ''
            }

    if data['constraints']:
        if data['args']: data['args'] = ',' + data['args']

    return constants.COLUMN % data

def foreignkeyconstraint_repr( self):

    data = {'name' : repr(self.name),
            'names' : repr([x.parent.name for x in self.elements]),
            'specs' : repr([x._get_colspec() for x in self.elements])
           }

    return constants.FOREIGN_KEY % data

def repr_index( index, tvarname):

    data = {'name' : repr(index.name),
            'columns' : ', '.join(['%s.c.%s' % (tvarname, c.name) for c in index.columns]),
            'unique' : repr(index.unique)
            } 

    return constants.INDEX % data

# Monkey patching sqlalchemy repr functions
sql._TextClause.__repr__ = textclause_repr
schema.Table.__repr__ = table_repr
schema.Column.__repr__ = column_repr
schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr

def printout(message, filehandle):
    """ Will print to stdout if filehandle is None """

    # it can happen that newlines are escaped during
    # dictionary evaluation because we're using raw data
    message = message.replace('\\n', '\n')

    if filehandle == None:
        print message
        return
        
    filehandle.write(message)

