class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name, description, function):
        self.tools[name] = {
            "description": description,
            "function": function
        }

    def list_tools(self):
        return {
            name: data["description"]
            for name, data in self.tools.items()
        }

    def get_tool(self, name):
        return self.tools.get(name)

    def execute(self, name, **kwargs):
        tool = self.get_tool(name)

        if not tool:
            raise ValueError(f"Tool '{name}' is not registered.")

        return tool["function"](**kwargs)
