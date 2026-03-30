"""
日志配置模块

模块作用:
    本模块负责配置应用程序的日志系统，使用 structlog 实现结构化日志输出。
    支持彩色控制台输出、上下文变量合并、异常信息格式化等功能。

使用场景:
    - 应用启动时调用 setup_logging() 初始化日志系统
    - 通过 get_logger() 获取日志记录器实例
    - 所有模块通过 logger 记录结构化日志，便于后续日志分析

在项目中的位置:
    位于 src/email_agent/logging_config.py，是应用的可观测性基础设施，
    被所有其他模块依赖用于记录运行日志。
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger


def add_app_name(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    为所有日志条目添加应用名称

    功能描述:
        作为 structlog 的 processor，在每条日志记录中添加应用标识符。
        便于在集中式日志系统中区分不同应用的日志。

    参数:
        logger: WrappedLogger 类型，日志记录器实例
        method_name: str 类型，被调用的日志方法名 (如 info, error 等)
        event_dict: EventDict 类型，当前日志事件字典

    返回值:
        EventDict: 添加了 app 字段的日志事件字典

    异常:
        无
    """
    # 添加应用名称标识，便于在多应用环境中区分日志来源
    event_dict["app"] = "email-agent"
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """
    配置应用程序的结构化日志系统

    功能描述:
        初始化 structlog 配置，设置日志处理器链，配置标准库日志系统。
        支持彩色控制台输出、异常追踪、上下文变量合并等功能。

    参数:
        log_level: str 类型，日志级别
            - "DEBUG": 调试级别，输出所有日志
            - "INFO": 信息级别，输出正常运行日志
            - "WARNING": 警告级别，输出潜在问题日志
            - "ERROR": 错误级别，输出错误日志
            - "CRITICAL": 严重级别，输出严重错误日志

    返回值:
        无

    异常:
        无

    配置说明:
        processors 链式处理:
        1. merge_contextvars: 合并上下文变量到日志事件
        2. add_log_level: 添加日志级别字段
        3. StackInfoRenderer: 渲染堆栈追踪信息
        4. add_app_name: 添加应用名称
        5. set_exc_info: 设置异常信息
        6. format_exc_info: 格式化异常信息
        7. ConsoleRenderer: 渲染到控制台 (带颜色)
    """
    # 配置 structlog 日志库
    structlog.configure(
        # 处理器链，按顺序处理每个日志事件
        processors=[
            # 合并异步上下文变量，支持 async/await 场景
            structlog.contextvars.merge_contextvars,
            # 添加日志级别字段 (info, error 等)
            structlog.processors.add_log_level,
            # 渲染堆栈追踪信息
            structlog.processors.StackInfoRenderer(),
            # 添加应用名称标识
            add_app_name,
            # 设置异常信息
            structlog.dev.set_exc_info,
            # 格式化异常信息为可读文本
            structlog.processors.format_exc_info,
            # 彩色控制台渲染器，便于开发调试
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        # 创建过滤日志记录器包装类，根据日志级别过滤
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        # 日志上下文使用 dict 存储
        context_class=dict,
        # 日志工厂使用 PrintLogger，输出到 stdout
        logger_factory=structlog.PrintLoggerFactory(),
        # 首次使用时缓存日志记录器，提高性能
        cache_logger_on_first_use=True,
    )

    # 配置 Python 标准日志库
    # 与 structlog 配合使用，处理底层日志输出
    logging.basicConfig(
        # 日志格式，仅使用消息字段 (structlog 处理其他格式)
        format="%(message)s",
        # 输出到标准输出
        stream=sys.stdout,
        # 设置日志级别
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> Any:
    """
    获取指定名称的日志记录器实例

    功能描述:
        创建或获取已缓存的 structlog 日志记录器。
        日志记录器名称通常使用模块的 __name__ 属性。

    参数:
        name: str 类型，日志记录器名称，通常使用 __name__

    返回值:
        Any: structlog 日志记录器实例，支持 info(), error(), warning() 等方法

    异常:
        无

    使用示例:
        logger = get_logger(__name__)
        logger.info("应用启动", version="0.1.0")
    """
    return structlog.get_logger(name)
