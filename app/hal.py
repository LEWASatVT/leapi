def makeLink():
    registry = {}
    def registrar(func):
        def wrapper(*args):
            return { "href": func(*args) }
        registry[func.__name__] = wrapper
        return wrapper

    registrar.all = registry
    return registrar

class HalView(object):
    link = makeLink()

    def _links(self):
        l = dict([ (rel,href(self)) for rel,href in HalView.link.all.items() ])
        try:
            l['curies'] = self.curies()
        except AttributeError:
            pass
        return l

class MetaHal(type):
    def __new__(cls,name, bases, attrs):
        attrs['link'] = makeLink()
        return type(name, (HalView,) + bases, attrs)
