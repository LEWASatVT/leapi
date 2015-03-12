import six
import itertools

from flask.ext.restplus.fields import Raw

class MarshallingException(Exception):
    """
    This is an encapsulating Exception in case of marshalling error.
    """
        
    def __init__(self, underlying_exception):
        # just put the contextual representation of the error to hint on what
        # went wrong without exposing internals
        super(MarshallingException, self).__init__(six.text_type(underlying_exception))

class Tuple(Raw):
    def __init__(self, *types, **kwargs):
        super(Tuple, self).__init__(**kwargs)
        self.types = []

        error_msg = ("The type of the list elements must be a subclass of "
                                          "flask_restful.fields.Raw")
        for cls_or_instance in types:
            if isinstance(cls_or_instance, type):
                self.types.append(cls_or_instance())
            else:
                self.types.append(cls_or_instance)
            # print("trying {}".format(cls_or_instance))
            # if isinstance(cls_or_instance, type):
            #     if not issubclass(cls_or_instance, Raw):
            #         raise MarshallingException(error_msg)
            #     self.types.append(cls_or_instance())
            # else:
            #     if not isinstance(cls_or_instance, Raw):
            #         raise MarshallingException(error_msg)
            #     self.types.append(cls_or_instance)

    def format(self, value):
        if isinstance(value, set):
            value = list(value)

        return [
            container.output(idx,
                val if (isinstance(val, dict)
                        or (container.attribute
                            and hasattr(val, container.attribute)))
                        and not isinstance(container, Nested)
                        and not type(container) is Raw
                    else value)
            for (idx, (container, val)) in enumerate(zip(self.types,value))
        ]
