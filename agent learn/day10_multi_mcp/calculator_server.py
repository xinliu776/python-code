from mcp.server import MCPServer

mcp=MCPServer("calculator")

@mcp.tool()
def add(a:int,b:int)->int:
    return a+b
@mcp.tool()
def subtract(a:int,b:int)->int:
    return a-b
@mcp.tool()
def multiply(a:int,b:int)->int:
    return a*b
@mcp.tool()
def divide(a:int,b:int)->int:
    return a/b