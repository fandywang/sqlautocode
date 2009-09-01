from sqlautocode.declarative import ModelFactory
class DummyConfig:
    engine = "postgres://postgres@localhost/TestUsers"
    schema = 'pdil_db'

class TestModelFactory:
    
    def setup(self):
        self.config = DummyConfig()
        self.factory = ModelFactory(self.config)
    
    def test_soup(self):
        soup = self.factory.soup
        soup.migrate_version
        import ipdb; ipdb.set_trace()