import typing as t

class FUNCTION_DECORATOR_API:
    """
    An interface defining the specification and key values
    for function decorators
    """
    # Properties
    PROPS = 'props'
    STATS_INPUT = 'input'
    FUNC_NAME = 'name'
    FUNCTION = 'func'
    DECORATED_WITH = 'decorated_with'

    # Used with callback
    CALLBACK = 'callback'


class ModuleApi:
    """
    An interface defining the keys for Module functions.
    """
    METHOD = "method"
    DECORATED = "decorated"
    CALL_CNT = "call_count"
    AVERAGE_EXECUTION_TIME = "exec_time"
    TOTAL_EXECUTION_TIME = "total_exec_time"

    @staticmethod
    def create_dict(method: t.Callable,
                    decorated: t.List = None,
                    call_cnt: int = 0):
        if decorated is None:
            decorated = []
        return {
            ModuleApi.METHOD: method,
            ModuleApi.DECORATED: decorated,
            ModuleApi.CALL_CNT: call_cnt,
            ModuleApi.TOTAL_EXECUTION_TIME: 0.0,
            ModuleApi.AVERAGE_EXECUTION_TIME: 0.0,
        }

    @staticmethod
    def update_stats(method_stats, elapsed):
        method_stats[ModuleApi.CALL_CNT] += 1
        method_stats[ModuleApi.TOTAL_EXECUTION_TIME] += elapsed
        method_stats[ModuleApi.AVERAGE_EXECUTION_TIME] = \
            method_stats[ModuleApi.TOTAL_EXECUTION_TIME] / method_stats[ModuleApi.CALL_CNT]
