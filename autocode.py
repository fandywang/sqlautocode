from sqlalchemy import *

import constants
from loader import *
from formatter import *

if __name__ == '__main__':

    import sys, getopt, os
    
    args, longargs = ('hu:o:s:t:i', ['help', 'url=', 'output=', 'schema=', 'tables=', 'noindex'])

    try:
        optlist, args = getopt.getopt(sys.argv[1:], args, longargs)
    except getopt.GetoptError:
        print >>sys.stderr, 'Error: Unknown arguments.'
        print >>sys.stderr, constants.USAGE
        sys.exit(255)
    
    if len(optlist)==0:
        print >>sys.stderr, 'Error: No arguments passed.'
        print >>sys.stderr, constants.USAGE
        sys.exit(0)

    url, output, schema, tables, filehandle, noindex, example = (None, None, None, None, None, None, False)
    for opt, arg in optlist:
        if opt in ['-h', '--help']:
            print >>sys.stderr, constants.USAGE
            sys.exit(0)
            
        if opt in ['-u', '--url']:
            url = arg

        if opt in ['-i', '--noindex']:
            noindex = True

        if opt in ['-e', '--example']:
            example = True
            
        if opt in ['-o', '--output']:
            output = arg

            if os.path.exists(output):
                print >>sys.stderr, 'Output file exists - it will be overwritten!'
                resp = raw_input('Overwrite (Y/N): ')
                if resp.strip().lower() != 'y':
                    print "Aborted."
                    sys.exit(0)

                else: os.unlink(output)

            filehandle = open(output, 'wU')
            
        if opt in ['-s', '--schema']:
            schema = arg.strip()
            
        if opt in ['-t', '--tables']:
            tables = arg.split(',')

    print >>sys.stderr, 'Starting...'
    dburl = engine.url.make_url(url)
    db = create_engine(url)
    try:
        autoloader = db.dialect.__class__.autoloader
    except AttributeError:
        print >>sys.stderr, 'Error: Unsupported db.dialect: ' + str(db.dialect)
        sys.exit(3)

    autoloader = autoloader(db)
    metadata = BoundMetaData(db)

    # some header with imports 
    printout(constants.HEADER, filehandle)
    
    tablenames = autoloader.table_names

    tbmapping = {}
    for tbname, tbschema in tablenames:
        if tbmapping.has_key(tbname) and schema != None:
            print >>sys.stderr, 'Error: Ambigous table name (%s) detected. Please specifiy a schema (--schema)!' % tbname
            if filehandle: filehandle.close()
            sys.exit(7)

        tbmapping[tbname] = tbschema
    
    # support user defined tables
    if tables != None:

        # first check if tables are available
        tablenames = []
        for tn in tables:
            tname = tn.strip()

            if tname[-1] != '*':

                # if user requested specific schema then we need to check that
                if schema != None:
                    if (tname, schema) not in autoloader.table_names:
                        print >>sys.stderr, 'Error: Table %s is not defined for schema %s' % (tname, schema)
                        if filehandle: filehandle.close()
                        sys.exit(5)

                # check that table is available
                else:
                    if tname not in tbmapping.keys():
                        print >>sys.stderr, 'Error: Table %s could not be found!' % tname
                        if filehandle: filehandle.close()
                        sys.exit(6)
                
                tablenames.append( (tname, tbmapping.get(tname)) )
                    
            # add support for globbed table names
            else:
                for t2name, tschema2 in autoloader.table_names:
                    if t2name.startswith(tname[:-1]):
                        if schema != None:
                            if tschema2 != schema:
                                print >>sys.stderr, 'Ignoring table %s (that would match %s) because schema does not match (%s)' % (t2name, tname, schema)
                                continue

                        tablenames.append( (t2name, tschema2) )

    for tname,tschema in tablenames:
        tname = tname.encode( 'utf-8')
        print >>sys.stderr, "Generating python model for table %s" % tname

        if tschema != None:
            table = Table(tname, metadata, schema=tschema, autoload=True)
        else:  table = Table(tname, metadata, autoload=True)

        if noindex != True:
            pindexes = constants.NLTAB.join(repr_index(index, tname)
                                        for index in autoloader.indexes(table) )
            if pindexes: 
                table.__indexdata__ = pindexes + ','
                
        for c in table.columns:
            c.type = autoloader.coltypes[ c.type.__class__ ]()
            
        printout('\n\n%s %s %s' % (tname, '=', repr(table)), filehandle)

    # print some example
    if example is True:
        printout('\n' + constants.FOOTER % {'url' : url, 'tablename' : tablenames[0][0]}, filehandle)
    
    if filehandle != None: 
        printout("\n", filehandle)
        filehandle.close()
        print >>sys.stderr, "Output written to %s" % output

# vim:ts=4:sw=4:expandtab
