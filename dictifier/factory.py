from .exceptions import FormatError


def node_validity(against):

    def wraper(node):
        node_is_valid = isinstance(node, against)
        if node_is_valid:
            return True
        else:
            message = f"Invalid Query format on \"{node}\" node."
            raise FormatError(message)

    return wraper


def query_validity(obj, query):
    flat_or_nested = all(
        map(node_validity((str, dict)), query)
    )

    iterable = (len(query) <= 1) and \
        all(
        map(node_validity((list, tuple)), query)
    )

    if flat_or_nested or iterable:
        return True
    else:
        return False


def _dict(obj, query, call_callable, not_found_create, fields=None):
    # Check if the query is valid against object
    assert query_validity(obj, query)
    for field in query:
        if isinstance(field, str):
            # Flat field
            if fields is None:
                     fields = {}
            if callable(getattr(obj, field)) and call_callable:
                fields.update({field: getattr(obj, field)()})
            else:
                fields.update({field: getattr(obj, field)})

        elif isinstance(field, dict):
            # Nested field or new field
            for sub_field in field:
                found = hasattr(obj, sub_field)

                if not_found_create and not found:
                    # Create new field
                    fields.update({sub_field: field[sub_field]})
                    continue
                elif not found:
                    # Throw NotFound Error [FIXME]
                    getattr(obj, sub_field)
                    continue

                if len(field[sub_field]) < 1:
                    # Nested empty object,
                    # Empty dict is the default value for empty nested objects.
                    # Comment the line below to remove empty objects in results. [FIXME]
                    fields.update({sub_field: {}})
                    continue

                if isinstance(field[sub_field][0], (list, tuple)):
                    # Nested object is iterable
                    fields.update({sub_field: []})
                else:
                    # Nested object is flat
                    fields.update({sub_field: {}})

                obj_field = getattr(obj, sub_field)
                if callable(obj_field) and call_callable:
                    obj_field = obj_field()

                _dict(
                    obj_field,
                    field[sub_field],
                    call_callable,
                    not_found_create,
                    fields=fields[sub_field],
                )

        elif isinstance(field, (list, tuple)):
            # Nested object
            if fields is None:
                     fields = []
            for sub_obj in obj:
                sub_field = {}
                fields.append(sub_field)
                _dict(
                    sub_obj,
                    field,
                    call_callable,
                    not_found_create,
                    fields=sub_field
                )
        else:
            message = f"""
                Wrong formating of Query on '{field}' node, It seems like the Query was mutated on run time.
                Use 'tuple' instead of 'list' to avoid mutating Query accidentally.
                """
            raise FormatError(message)

    return fields
