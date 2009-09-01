import sys
from util import emit
from sqlalchemy.ext.sqlsoup import SqlSoup



class ModelFactory(object):
    
    def __init__(self, config):
        self.config = config
        
    @property
    def soup(self):
        if hasattr(self, '_soup'):
            return self._soup
        s = SqlSoup(self.config.engine)
        schema = getattr(self.config, 'schema', None)
        if schema:
            s.schama = schema
        self._soup = s
        return s
