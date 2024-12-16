class ContextStore:
    def __init__(self, type: str, contexts: dict[str, object]):
        self.type = type
        self.contexts = contexts

    def get_context_data(self, name):
        return self.contexts.get(name, None)

    def get_contexts(self, dependencies: list[str] | str = "*"):
        if dependencies == "*":
            return self.contexts
        elif isinstance(dependencies, (list, tuple)):
            return {
                name: context
                for name, context in self.contexts.items()
                if name in dependencies
            }
        return {}
