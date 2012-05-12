def pytest_funcarg__ec(request):
    # Inside the function so various intitialization stuff isn't seen until
    # coverage is setup.
    from rupypy.objspace import ObjectSpace
    from rupypy.executioncontext import ExecutionContext

    return ExecutionContext(ObjectSpace())
