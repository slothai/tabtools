class ProxyMeta(type):

    """ Proxy objects metaclass. """

    __store__ = dict()

    def __new__(class_, name, bases, params):
        cls = super(ProxyMeta, class_).__new__(class_, name, bases, params)

        if not cls.__proxy__:
            cls.__proxy__ = cls
            class_.__store__[cls] = dict()
            return cls

        proxy = cls.__proxy__.__name__
        key = ''.join(s for s in name.split(proxy, 1) if s).lower()
        cls.proxy = property(lambda x: x)
        class_.__store__[cls.__proxy__][key] = cls
        return cls


class Proxy(object):

    """ Proxy class functionality. """

    __proxy__ = None

    @property
    def proxy(self):
        """ Return instance with related proxy class. """
        proxy_base = self.__class__.__proxy__
        cls = self.__class__.__store__[proxy_base].get(self.key, proxy_base)
        new = cls.__new__(cls)
        new.__dict__ = self.__dict__
        return new


class _classproperty(property):

    """ Implement property behaviour for classes.
    class A():
        @_classproperty
        @classmethod
        def name(cls):
            return cls.__name__
    """

    def __get__(self, obj, type_):
        return self.fget.__get__(None, type_)()


def _cached(f):
    ''' Decorator that makes a method cached.'''

    attr_name = '_cached_' + f.__name__

    def wrapper(obj, *args, **kwargs):
        if not hasattr(obj, attr_name):
            setattr(obj, attr_name, f(obj, *args, **kwargs))
        return getattr(obj, attr_name)
    return wrapper


classproperty = lambda f: _classproperty(classmethod(f))
cached_property = lambda f: property(_cached(f))
cached_classproperty = lambda f: classproperty(_cached(f))
