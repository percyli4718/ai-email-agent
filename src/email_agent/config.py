"""
配置管理模块

模块作用:
    本模块负责管理应用程序的所有配置项，通过 pydantic-settings 从环境变量加载配置。
    提供了类型安全的配置访问接口，支持默认值和验证。

使用场景:
    - 应用启动时加载环境变量到配置对象
    - 为其他模块提供统一的配置访问入口
    - 支持开发/生产环境的不同配置

在项目中的位置:
    位于 src/email_agent/config.py，是应用的基础设施层，被几乎所有其他模块依赖。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    应用程序配置类

    作用:
        定义应用程序的所有配置项，通过环境变量自动填充。
        使用 pydantic 进行类型验证和默认值管理。

    使用场景:
        - 应用启动时实例化，加载所有配置
        - 通过依赖注入传递给需要配置的组件
        - 支持测试时覆盖配置值

    主要属性:
        anthropic_api_key: Anthropic API 密钥，用于调用 Claude 模型
        ollama_host: Ollama 服务地址，用于本地 embedding 生成
        database_url: 数据库连接 URL
        chroma_persist_dir: ChromaDB 向量数据库持久化目录
        env: 运行环境 (development/production)
        log_level: 日志级别
        default_agent_budget: Agent 默认预算上限 (美元)
        max_sonnet_cost_per_email: 每封邮件使用 Sonnet 模型的最大成本
        max_opus_cost_per_email: 每封邮件使用 Opus 模型的最大成本
        target_sonnet_rate: 目标 Sonnet 路由率 (成本控制，默认 80%)
    """

    model_config = SettingsConfigDict(
        # 从 .env 文件加载环境变量
        env_file=".env",
        # 环境变量名称不区分大小写
        case_sensitive=False,
        # 忽略未定义的额外字段
        extra="ignore"
    )

    # Anthropic API 配置
    # 用于访问 Claude 模型的 API 密钥
    anthropic_api_key: str = Field(default="test-key")

    # Ollama 本地服务配置
    # 用于运行本地 embedding 模型 (如 mxb3embed-base)
    ollama_host: str = Field(default="localhost:11434")

    # 数据库配置
    # 使用 SQLite + aiosqlite 作为异步数据库驱动
    database_url: str = Field(default="sqlite+aiosqlite:///./data/email_agent.db")

    # ChromaDB 向量数据库配置
    # 用于存储和检索历史邮件的 embedding 向量
    chroma_persist_dir: str = Field(default="./data/chroma")

    # 应用运行环境配置
    # development: 开发环境，启用热重载
    # production: 生产环境，禁用调试功能
    env: str = Field(default="development")

    # 日志级别配置
    # 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_level: str = Field(default="INFO")

    # 成本控制配置
    # 每个 Agent 操作的默认预算上限 (美元)
    default_agent_budget: float = Field(default=1.0)

    # 每封邮件使用 Claude Sonnet 模型的最大成本 (美元)
    max_sonnet_cost_per_email: float = Field(default=0.02)

    # 每封邮件使用 Claude Opus 模型的最大成本 (美元)
    max_opus_cost_per_email: float = Field(default=0.10)

    # 目标 Sonnet 路由率
    # 根据 JD 要求，80% 的请求应该路由到成本更低的 Sonnet 模型
    target_sonnet_rate: float = Field(default=0.80)

    # LLM Provider 配置
    # 支持的 provider: "anthropic", "bailian", "mock"
    llm_provider: str = Field(default="anthropic")

    # 阿里百炼配置
    bailian_api_key: str = Field(default="")
    bailian_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    bailian_model: str = Field(default="qwen-max")


# 全局 Settings 实例
# 在模块导入时创建，供整个应用共享使用
settings = Settings()


def get_settings() -> Settings:
    """
    获取 Settings 实例的依赖注入函数

    功能描述:
        为 FastAPI 依赖注入系统提供 Settings 实例。
        在测试环境中可以方便地覆盖配置。

    参数:
        无

    返回值:
        Settings: 全局 Settings 实例

    异常:
        无
    """
    return settings
