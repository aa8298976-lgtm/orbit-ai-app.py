from tools.registry import ToolRegistry


class ToolExecutor:

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, tool_name, **kwargs):
        tool = self.registry.get_tool(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found."
            }

        try:
            result = tool["function"](**kwargs)

            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }

        except Exception as error:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(error)
            }
