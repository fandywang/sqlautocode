AutoCode is a flexible tool to autogenerate a model from an existing database.

This is a slightly different approach to SqlSoup, 
that lets you use tables without explicitly defining them.

Current Maintainer:
    
    Simon Pamies (spamsch)
    E-Mail: s.pamies at banality dot de

Authors:

    Paul Johnson (original author)
    
    Christophe de Vienne (cdevienne)
    E-Mail: cdevienne at gmail dot com

    Svilen Dobrev (sdobrev)
    E-Mail: svilen_dobrev at users point sourceforge dot net

License:
    
    MIT
    see license.txt

Requirements:

    sqlalchemy 0.3.9+
    Not known to work with 0.4!

Documentation:

    Call autocode.py --help for a list of available self explaining options.

    Example:
    autocode.py -o model.py -u postgres://postgres:user@password/MyDatabase -s myschema -t Person*,Download

ToDo:

    + Test with different dialects
    + Add support for automagically creating relations
    + Generate ActiveMapper / Elixir model

Notes (random):

    metadata stuff from:
    http://sqlzoo.cn/howto/source/z.dir/tip137084/i12meta.xml

