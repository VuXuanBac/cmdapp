from cmdapp.utils import Json


def contains_all(text: str, substrings: list[str], ignore_case=True):
    if ignore_case:
        text = text.lower()
        substrings = [str(sub).lower() for sub in substrings]
    return all(sub in text for sub in substrings)


def has_attributes(o1, o2: dict, *, serializer=None):
    return all(
        same_data(getattr(o1, attr), value, serializer=serializer)
        for attr, value in o2.items()
    )


def same_data(o1, o2, *, serializer=None):
    """Compare two objects are equal by data (not need at same type)

    Args:
        o1: Object to compare
        o2: Object to compare
        serializer (Callable, optional): Serializer to serialize complex data. Defaults to None.

    Returns:
        bool: True if they are equal
    """
    o1_json = Json.dump(o1, sort_keys=True, default=serializer)
    o2_json = Json.dump(o2, sort_keys=True, default=serializer)
    return o1_json == o2_json


def get_output(caller, input, pass_directly=False):
    """Run a function with input and return the output.

    Input was passed with following conventions:
    - If `pass_directly = True` or the caller is a <lambda>:
      - Pass input directly (single argument)
    - If it is a LIST or TUPLE:
      - If has at least 2 items the last item is a DICT: Pass all except last as *args, pass the last as **kwargs
      - Else: Pass all as *args
    - If it is a DICT: Pass all as **kwargs
    - DEFAULT case: Pass directly

    Args:
        caller (Callable): Function to run
        input (Any): Input to pass into the caller.
        pass_directly (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    if not caller:
        return input
    if pass_directly or caller.__name__ == "<lambda>":
        return caller(input)
    elif isinstance(input, (list, tuple)):
        if len(input) > 1:
            kwargs = input[-1]
            if isinstance(kwargs, dict):
                return caller(*input[:-1], **kwargs)
        return caller(*input)
    elif isinstance(input, dict):
        return caller(**input)
    else:

        return caller(input)


########## Decorators ##########
def with_cases(
    handler, inputs: dict[str], expects: dict[str], pass_directly=False, **kwargs
):
    """A decorator to test one function with different named-cases
    - The decorated function should have following arguments:
        - output: Runned output or a tuple of (error type, str(error)) if have any exception
        - expect: Expected output
        - case: Name of the case
    - For each input-expect pair, run the function with the input and capture the output

    Args:
        handler (Callable): Function to test
        inputs (dict[str]): Inputs to the method with name of the case
        expects (dict[str]): Expected output with name of the case
        pass_directly (bool, optional): True to pass the input dict directly (one argument) to the method. Defaults to False.
        kwargs: Default arguments to `input`. Only used if `input` is a dict and not pass directly (means, it is passed by keywords)
    """

    def decorator(func):
        def body():
            for case, input in inputs.items():
                try:
                    if kwargs and isinstance(input, dict) and not pass_directly:
                        input = kwargs | input
                    output = get_output(handler, input, pass_directly=pass_directly)
                except Exception as ex:
                    print("EXCEPTION", ex)
                    output = (type(ex).__name__, ex.args)
                func(output, expects.get(case, None), case)

        return body

    return decorator


def with_object(
    object_creator,
    method_name: str,
    inputs: dict[str, dict],
    expects: dict[str, object],
    pass_directly=False,
    *args,
    **kwargs
):
    """A decorator to test one method on same object with different named-cases
    - The decorated function should have following arguments:
        - object: Created object
        - output: Runned output or a Tuple of (error type, str(error)) if have any exception
        - expect: Expected output
        - case: Name of the case
    - For each input-expect pair, run the method with the input and capture the output

    Args:
        object_creator (Callable): Function to create object. Use arguments from *args and **kwargs of the decorator function
        method_name (str): Name of the method to test (get from created object)
        inputs (dict[str, dict]): Inputs to the method with name of the case
        expects (dict[str, object]): Expected output with name of the case
        pass_directly (bool, optional): True to pass the input dict directly (one argument) to the method. Defaults to False.
        args: Arguments pass into the object_creator
        kwargs: Arguments pass into the object_creator
    """

    def decorator(func):
        def body():
            for case, input in inputs.items():
                object = object_creator(*args, **kwargs)
                method = getattr(object, method_name)
                try:
                    output = get_output(method, input, pass_directly=pass_directly)
                except Exception as ex:
                    print("EXCEPTION", ex)
                    output = (type(ex).__name__, ex.args)
                func(object, output, expects.get(case, None), case)

        return body

    return decorator
