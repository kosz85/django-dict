=================================
    django-dict
=================================

Django dict is model transformer. When you use JSON's or just need some dicts, you can just do obj.to_dict() and it will fetch objects and format them.
More docs are in doc strings in ToDictClass.

Example
=======

.. code-block:: python

    import todict
    from django.db import models
    
    # Example from django docs + todict
    class Musician(models.Model, todict.ToDictClass):
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        instrument = models.CharField(max_length=100)
    
    class Album(models.Model, todict.ToDictClass):
        artist = models.ForeignKey(Musician)
        name = models.CharField(max_length=100)
        release_date = models.DateField()
        num_stars = models.IntegerField()
    
    # And what we can do now
    
    musician = Musician.objects.all()[0]
    
    # return as dict
    >>> musician.to_dict()
    {
        'id': 0,
        'first_name': 'Bla',
        'last_name': 'Ble',
        'instrument': 'guitar',
        'album': [1,5]
    }
    
    # return only selected fields
    >>> musician.to_dict("first_name")
    {
        'first_name': 'Bla'
    }
    
    # return all fields exluding some
    >>> musician.to_dict("-first_name")
    {
        'id': 0,
        'last_name': 'Ble',
        'instrument': 'guitar',
        'album': [1,5]
    }
    
    # fetch related objects and select fields from them
    >>> musician.to_dict("first_name album! album|name")
    {
        'first_name': 'Bla'
        'album': [{'name': 'first album'}, {'name': 'second album'}]
    }

    # filter related objects
    >>> musician.to_dict("first_name album(name__startswith=second)! album|name")
    {
        'first_name': 'Bla',
        'album': [{'name': 'second album'}]
    }

    # move data
    >>> musician.to_dict("first_name album(name__startswith=second)! album|!0|name:album_name")
    {
        'first_name': 'Bla',
        'album': [{}],
        'album_name': 'second album'
    }

    # delete keys after processing
    >>> musician.to_dict("first_name album(name__startswith=second)! album|!0|name:album_name ~album")
    {
        'first_name': 'Bla',
        'album_name': 'second album'
    }

    # rename keys
    >>> musician.to_dict("first_name=>name")
    {
        'name': 'Bla'
    }
    
    

And it all works on normal dicts.

.. code-block:: python

    import todict
    my_dict = todict.FormatedDict({'a': 1, 'b': {'c': 'd', 'e': {'f'}}})
    
    >>> my_dict.to_dict('a')
    {
        'a': 1
    }
    
    # but my_dict is still the same
    >>> my_dict
    {'a': 1, 'b': {'c': 'd', 'e': {'f'}}}
    
    # and like in django examples, but without fetch feture, you can move, copy, delete, exclude, etc.
    
TODO or wish list
=======
- Tests - it is already tested in a quite big app, but it would be nice to have own specyfic test cases for this lib.
- Performance - there is nothing to complain, but in future maybe some optional low level dict operations or format parsing tools would be written.
- Better fetch - fetch is complicated, current version don't support fetching twice same field with another set of filters.
- Using prefetched data - look at my another projects
- Better format parsing - there is some pyparse parsing in alfa version with some nice fetures, but not fully working - maybe in some time

WARNINGS
=========
- fetch has it's own humors, for our cases it's working, but you can have problems with spaces in filter arguments witch are not allowed for now.
- you can fetch field in fetch in fetch, but it's not very performant way of getting data especially when using filters (no prefetches)
- it's addictive and can save too much of your time ;) We ended with to_dicts everywhere.
- look in the docs for special hooks and cases.
