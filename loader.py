
from sqlalchemy.databases import postgres
from sqlalchemy.databases import mssql
from sqlalchemy.databases import sqlite
from sqlalchemy.databases import information_schema

from sqlalchemy import *
import constants

class AutoLoader:
    pass

class AutoLoader4postgress( AutoLoader):
    coltypes = dict( (v,k) for k,v in postgres.pg2_colspecs.iteritems() )
    
    # selecting all tables available in all schemas - the schema constraint
    # is passed later on by user request
    sql4tables = text( "SELECT tablename,schemaname FROM pg_tables")
    sql4indexes = text( "SELECT indexname, tablename, indexdef FROM pg_indexes" )

    def __init__( me, db):
        me.table_names = [ (name,schemaname) for (name,schemaname) in db.execute(me.sql4tables) ]
        
        me._indexes = ix = {}
        for name,tbl_name,sqltext in db.execute( me.sql4indexes):
            ix.setdefault( tbl_name, [] ).append( (name,sqltext) )

    def _index_from_def( me, name, sqltext, table):
        # CREATE UNIQUE INDEX name ON "tablename" USING btree (columnslist)
        unique = ' UNIQUE ' in sqltext
        cols = sqltext.split(' (')[1].split(')')[0].split(',')
        cols = [ table.columns[ cname.strip().replace('"', '') ] for cname in cols]
        name = name.encode( 'utf-8')
        return Index( name, unique=unique, *cols )

    def indexes( me, table):
        return [ me._index_from_def( name, sqltext, table)
                    for name,sqltext in me._indexes.get( table.name, () )
                ]
                
postgres.PGDialect.autoloader = AutoLoader4postgress

class AutoLoader4mssql( AutoLoader):
    coltypes = dict( (v,k) for k,v in mssql.MSSQLDialect.colspecs.iteritems() )
    def __init__( me, db):
        itables = information_schema.tables
        sqltext = select(
                [itables.c.table_name, itables.c.table_schema],
                itables.c.table_schema==dburl.database
            )
        me.table_names = db.execute( sqltext)

    def indexes( me, table): return table.indexes
    
mssql.MSSQLDialect.autoloader = AutoLoader4mssql

class AutoLoader4sqlite( AutoLoader4postgress):
    sqlite_master = constants.SQLITE_MASTER
    coltypes = dict( (v,k) for k,v in sqlite.colspecs.iteritems() )
    sql4tables  = text( "SELECT name FROM sqlite_master WHERE type='table'")
    sql4indexes = text( "SELECT name,tbl_name,sql FROM sqlite_master WHERE type='index'" )

sqlite.SQLiteDialect.autoloader = AutoLoader4sqlite

