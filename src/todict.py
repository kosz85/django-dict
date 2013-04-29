import collections

try:
    from django.db.models.fields.related import (ForeignKey, RelatedObject,
                                                 ManyToManyField)
except ImportError:
    # Fallback when todict was used without django
    pass


class FormatedDict(dict):
    def __init__(self, *args, **kwargs):
        self.format = 'format' in kwargs and kwargs.pop('format') or None
        super(FormatedDict, self).__init__(*args, **kwargs)

    def to_dict(self, format=None, separator='|', postprocess=None, **kwargs):
        """
        additional kwargs:
            separator - default '|'
            postprocess - func called once on the end on returned dict
            fields
            exclude
            move
            copy
            remove
            rename
            convert
        """
        key = lambda name: kwargs.get('rename', {}).get(name, name)
        cnv = lambda value: kwargs.get('convert', {}).get(type(value),
                                                          lambda v: v)(value)
        exc = lambda name: not ((not kwargs.get('fields') or
                                 name in kwargs.get('fields', [])) and
                                (not kwargs.get('exclude') or
                                 name not in kwargs.get('exclude', [])))

        def get_kwargs(name, kw):
            return {
                'separator': separator,
                'fields': [separator.join(n.split(separator)[1:])
                           for n in kw.get('fields') or []
                           if n.split(separator)[0] == name
                           and len(n) > len(name)],
                'exclude': [separator.join(n.split(separator)[1:])
                            for n in kw.get('exclude') or []
                            if n.split(separator)[0] == name
                            and len(n) > len(name)],
                'rename': {separator.join(n.split(separator)[1:]): v
                           for n, v in (kw.get('rename') or {}).items()
                           if n.split(separator)[0] == name
                           and len(n) > len(name)},
                'convert': kw.get('convert') or {},
            }

        if not format and self.format:
            format = self.format
        if format:
            kwargs = Format(format).get_kwargs()

        d = {}
        for name, value in self.items():
            if exc(name):
                continue
            elif isinstance(value, dict):
                value = FormatedDict(value).to_dict(**get_kwargs(name, kwargs))
            elif isinstance(value, list):
                for i in xrange(len(value)):
                    if isinstance(value[i], dict):
                        value[i] = FormatedDict(value[i]).to_dict(
                            **get_kwargs(name, kwargs))
                    else:
                        break
            d[key(name)] = cnv(value)

        replace = [(k, v, FormatedDict._mv)
                   for k, v in kwargs.get('move', {}).items()]
        replace += [(k, v, FormatedDict._cp)
                    for k, v in kwargs.get('copy', {}).items()]
        replace.sort(reverse=True)
        for r in replace:
            r[2](d, r[0].split(separator), r[1].split(separator))
        for r in kwargs.get('remove', []):
            FormatedDict._rm(d, r.split(separator))

        if postprocess:
            return postprocess(d)
        else:
            return d

    @staticmethod
    def _get_path(d, path, create=False):
        for pa in path:
            if pa.startswith('!'):
                pa = int(pa[1:])
                if not hasattr(d, '__len__') or pa >= len(d):
                    raise NotFound
                d = d[pa]
            else:
                if d is None:
                    raise NotFound
                if pa not in d:
                    if create:
                        d[pa] = {}
                    else:
                        raise NotFound
                d = d[pa]
        return d

    @staticmethod
    def _rm(d, path):
        p = d
        for pa in path[:-1]:
            if pa.startswith('!'):
                pa = int(pa[1:])
            if not hasattr(p, '__len__') or pa >= len(p):
                return d
            p = p[pa]
        pa = path[-1]
        if pa.startswith('!'):
            pa = int(pa[1:])
        if not hasattr(p, '__len__') or pa >= len(p):
            del p[pa]
        return d

    @staticmethod
    def _cp(d, path_from, path_to):
        try:
            target = FormatedDict._get_path(d, path_to[:-1], create=True)
            target[path_to[-1]] = FormatedDict._get_path(d, path_from)
        except NotFound:
            pass
        return d

    @staticmethod
    def _mv(d, path_from, path_to):
        try:
            source = FormatedDict._get_path(d, path_from[:-1])
            target = FormatedDict._get_path(d, path_to[:-1], create=True)
            target[path_to[-1]] = FormatedDict._get_path(source,
                                                         [path_from[-1]])
            FormatedDict._rm(source, [path_from[-1]])
        except NotFound:
            pass
        return d


class Format(unicode):
    def join_format(self, pre, format):
        return Format(' '.join(self.split() + [pre + s
                                               for s in format.split()]))

    @staticmethod
    def get_filter(field):
        """ return processed field_name and filter kwargs in form:
            field(filter=value)(order)"""
        if not field.endswith(')'):
            return field, {}, []
        start = field.find('(')
        order_start = field.find(')(')
        end = order_start if order_start > -1 else -1
        filt = field[start + 1: end]
        order = field[order_start != -1 and order_start + 2 or -1: -1]
        field = field[:start]
        return field, \
            filt and dict([s.strip().split('=')
                           for s in filt.split(',')]) or {}, \
            order and [o.strip() for o in order.split(',')] or []

    @staticmethod
    def fetch_to_dict(fetch):
        fetch_dict = collections.defaultdict(lambda: ({}, []))
        for f in fetch or []:
            k, v, o = Format.get_filter(f)
            fetch_dict[k] = (v, o)
        return fetch_dict

    def get_kwargs(self):
        format = self.split(' ')
        fields = []
        exclude = []
        fetch = []
        move = {}
        copy = {}
        remove = []
        rename = {}
        ex = False
        for f in format:
            path_to = None
            f = f.strip()
            if '=>' in f:
                field, path_to = f.split('=>')
            elif '#' in f and ':' in f:
                raise ValueError("'#' and ':' must be used separately")
            elif '#' in f:
                if path_to:
                    raise ValueError("'#' and '=>' must be used separately")
                field, path_to = f.split('#')
            elif ':' in f:
                if path_to:
                    raise ValueError("':' and '=>' must be used separately")
                field, path_to = f.split(':')
            else:
                field = f

            if field.endswith('!'):
                field = field[:-1]
                tmpf = field[1:] if field.startswith('-') else field
                # here is reducing field(..) to filed
                ind = field.find('(')
                field = field[:ind] if ind > -1 else field
                fetch.append(tmpf.replace('~', ''))
            if field.startswith('-'):
                ex = True
                field = field.replace('-', '')
                exclude.append(field.replace('~', ''))
            if field.startswith('~'):
                field = field.replace('~', '')
                remove.append(field)
            fields.append(field)
            if '#' in f:
                copy[field] = path_to
            elif ':' in f:
                move[field] = path_to
            elif '=>' in f:
                rename[field] = path_to
        if ex:
            fields = None

        return {
            'fields': fields,
            'exclude': exclude,
            'fetch_dict': Format.fetch_to_dict(fetch),
            'fetch': fetch,
            'move': move,
            'copy': copy,
            'remove': remove,
            'rename': rename
        }


class NotFound(Exception):
    pass


class ToDictClass(object):
    def to_dict(instance, format=None, separator='|', **kwargs):
        """ Returns a dictionary containing field names and values
        for the given instance and much more.

        1. fields filtering cheking fields and exclude
        2. fetching related models (on default it return ids)
        3. convert values (for examle {Decimal: str}
        4. rearange data via move and copy dicts
            service|name --> service_name
            order --> ordering etc.
            region|name --> location|zipcode

        Params:
            format - high level representation of all params except convert and
                    separator (see below)
            separator - seperates nested fields (default '|' )
            fields - :list: exclude everything not listed (preprocesing)
            exclude - :list: exclude everthing listed (preprocsesing)
            fetch - :list: fetch content of listed relations
            move - :dict: move path to new localisation
            copy - :dict: copy path to new path (faster then move)
            remove - :list: remove everything listed (postprocessing)
            rename - :dict: rename attributes
            convert - :dict: {type: func} cast/modify values of some type

        You can access name of second element of the list using path:
        some_related_field|!2|name
        ! - it's a special character, if there won't be such index it would be
        ignored

        Format:
            field! - fetch
            field(id=12) - fetch with filter
            -field - exclude
            ~field - remove
            field - fields
            field:path - move
            field#path - copy
            field|field - nested field
            field=>new_name - rename
        Warnings:
            You can't use : and # in one sentence like this: field:path#path
                instead do this: field:path field#path
            You can use field -field! but it makes no sense. Field will
                be excluded so no fetch would happen.
            When exclude is not used, it will return only specified fields.
            You can use -not_existent_field to return all

        So
        ~field!#path - fetches relative field copy to new location and
                       removes old location

        ~field! field|another_field#path
        is faster than
        ~field! field|another_field:path
        """
        key = lambda name: kwargs.get('rename', {}).get(name, name)
        cnv = lambda value: kwargs.get('convert', {}).get(type(value),
                                                          lambda v: v)(value)
        exc = lambda name: not ((not kwargs.get('fields') or
                                 name in kwargs.get('fields', [])) and
                                (not kwargs.get('exclude') or
                                 name not in kwargs.get('exclude', [])))

        def get_kwargs(name, kw):
            return {
                'separator': separator,
                'fetch': [separator.join(n.split(separator)[1:])
                          for n in kw.get('fetch') or []
                          if n.split(separator)[0] == name
                          and len(n) > len(name)],
                'fields': [separator.join(n.split(separator)[1:])
                           for n in kw.get('fields') or []
                           if n.split(separator)[0] == name
                           and len(n) > len(name)],
                'exclude': [separator.join(n.split(separator)[1:])
                            for n in kw.get('exclude') or []
                            if n.split(separator)[0] == name
                            and len(n) > len(name)],
                'rename': {separator.join(n.split(separator)[1:]): v
                           for n, v in (kw.get('rename') or {}).items()
                           if n.split(separator)[0] == name
                           and len(n) > len(name)},
                'convert': kw.get('convert') or {},
            }

        if format:
            kwargs.update(Format(format).get_kwargs())
            fetch_dict = kwargs.get('fetch_dict')
        else:
            fetch_dict = Format.fetch_to_dict(kwargs.get('fetch'))

        fetch_keys = fetch_dict.keys()
        d = FormatedDict()
        meta = instance._meta
        for name in meta.get_all_field_names():
            if exc(name):
                continue
            ftype = meta.get_field_by_name(name)[0]
            if isinstance(ftype, RelatedObject):
                value = getattr(
                    instance,
                    name,
                    getattr(instance, ftype.get_accessor_name())
                )
                query = value.filter(**fetch_dict[name][0])
                if fetch_dict[name][1]:
                    query = query.order_by(*fetch_dict[name][1])
                if name in fetch_keys:
                    d[key(name)] = [ro.to_dict(**get_kwargs(name, kwargs))
                                    for ro in query]
                else:
                    d[key(name)] = [ro.id for ro in query.only('id')]
                continue

            value = getattr(instance, name)
            if isinstance(ftype, ManyToManyField):
                query = value.filter(**fetch_dict[name][0])
                if fetch_dict[name][1]:
                    query = query.order_by(*fetch_dict[name][1])

                if name in fetch_keys:
                    d[key(name)] = [ro.to_dict(**get_kwargs(name, kwargs))
                                    for ro in query]
                else:
                    d[key(name)] = [ro.id for ro in query.only('id')]
                continue

            if value is not None and isinstance(ftype, ForeignKey):
                if name in fetch_keys:
                    value = value.to_dict(**get_kwargs(name, kwargs))
                else:
                    value = value._get_pk_val()
            elif isinstance(ftype, RelatedObject):
                value = [ro.to_dict(**get_kwargs(name, kwargs))
                         for ro in value.all()]
            else:  # Normal field
                value = cnv(value)
            d[key(name)] = value
        if 'fields' in kwargs:
            del kwargs['fields']
        if 'exclude' in kwargs:
            del kwargs['exclude']
        kwargs['separator'] = separator
        return d.to_dict(**kwargs)
