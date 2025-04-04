# Run before cmdloop
PREPARE_HOOK_PREFIX = "prepare_"

# Run after parsing input and before running the cmd
VALIDATE_HOOK_PREFIX = "validate_"

# Run after running the cmd
RENDER_HOOK_PREFIX = "render_"

# Run after cmdloop
FINALIZE_HOOK_PREFIX = "finalize_"


def get_attributes_by_prefix(cls, prefix: str):
    attributes = dir(cls)
    return {
        key[len(prefix) :]: getattr(cls, key)
        for key in attributes
        if key.startswith(prefix)
    }


class Hook:
    def __init__(self):
        pass

    @classmethod
    def get_prepare_hooks(cls):
        return get_attributes_by_prefix(cls, PREPARE_HOOK_PREFIX)

    @classmethod
    def get_finalize_hooks(cls):
        return get_attributes_by_prefix(cls, FINALIZE_HOOK_PREFIX)

    @classmethod
    def get_validate_hooks(cls):
        return get_attributes_by_prefix(cls, VALIDATE_HOOK_PREFIX)

    @classmethod
    def get_render_hooks(cls):
        return get_attributes_by_prefix(cls, RENDER_HOOK_PREFIX)
