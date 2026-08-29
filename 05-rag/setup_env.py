# 文件名：setup_env.py
"""
RAG教程环境自动配置脚本
自动安装所有必需的库和依赖
"""

import subprocess
import sys
import os

def run_command(command, description):
    """
    运行shell命令并显示进度

    Args:
        command: 要执行的命令
        description: 命令描述
    """
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"{'='*60}")
    print(f"命令: {command}\n")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} - 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - 失败")
        print(f"错误: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python版本过低，需要3.9或更高")
        return False

    print("✓ Python版本符合要求")
    return True

def install_core_packages():
    """安装核心包"""
    packages = [
        # LlamaIndex核心
        "llama-index-core",
        "llama-index-llms-openai",
        "llama-index-embeddings-openai",
        "llama-index-vector-stores-chroma",

        # 向量数据库
        "chromadb",

        # 文档处理
        "pypdf",
        "docx2txt",
        "python-dotenv",

        # 数据处理
        "pandas",
        "numpy",

        # 可视化
        "matplotlib",
        "seaborn",

        # 实用工具
        "tqdm",  # 进度条
        "rich",  # 美化终端输出
    ]

    print("\n开始安装核心包...")
    for package in packages:
        run_command(f"pip install -U {package}", f"安装 {package}")

    return True

def install_optional_packages():
    """安装可选包"""
    optional = [
        "llama-index-readers-web",  # 网页抓取
        "llama-index-readers-file", # 文件读取
        "sentence-transformers",    # 开源嵌入模型
        "transformers",             # HuggingFace
    ]

    print("\n是否安装可选包？(包含网页抓取、开源模型等)")
    choice = input("输入 y 安装，其他键跳过: ").strip().lower()

    if choice == 'y':
        for package in optional:
            run_command(f"pip install -U {package}", f"安装 {package}")

    return True

def create_env_template():
    """创建环境变量模板文件"""
    env_content = """# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1  # 可选：使用代理或兼容API

# 其他配置
CHROMA persist_directory=./chroma_db
"""

    with open(".env.template", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n✓ 已创建 .env.template 文件")
    print("  请复制为 .env 并填入你的API密钥")
    return True

def create_project_structure():
    """创建项目目录结构"""
    directories = [
        "data/raw",           # 原始数据
        "data/processed",     # 处理后数据
        "notebooks",          # Jupyter notebooks
        "scripts",            # Python脚本
        "outputs",            # 输出结果
        "chroma_db",          # 向量数据库
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

    return True

def create_requirements_txt():
    """生成requirements.txt"""
    requirements = """# RAG教程依赖

# 核心
llama-index-core>=0.10.0
llama-index-llms-openai>=0.1.0
llama-index-embeddings-openai>=0.1.0
llama-index-vector-stores-chroma>=0.1.0

# 向量数据库
chromadb>=0.4.0

# 文档处理
pypdf>=3.0.0
docx2txt>=0.8
python-dotenv>=1.0.0

# 数据处理
pandas>=2.0.0
numpy>=1.24.0

# 可视化
matplotlib>=3.7.0
seaborn>=0.12.0

# 工具
tqdm>=4.65.0
rich>=13.0.0

# 可选
llama-index-readers-web>=0.1.0
llama-index-readers-file>=0.1.0
sentence-transformers>=2.2.0
"""

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)

    print("\n✓ 已创建 requirements.txt 文件")
    return True

def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║       RAG教程 - 环境自动配置工具                      ║
    ║       自动安装所有必需的库和依赖                      ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # 1. 检查Python版本
    if not check_python_version():
        return False

    # 2. 安装核心包
    if not install_core_packages():
        return False

    # 3. 安装可选包
    install_optional_packages()

    # 4. 创建项目结构
    print("\n创建项目目录结构...")
    create_project_structure()

    # 5. 创建配置文件
    create_env_template()
    create_requirements_txt()

    print(f"""
    {'='*60}
    ✓ 环境配置完成！
    {'='*60}

    下一步：
    1. 配置OpenAI API密钥：
       cp .env.template .env
       编辑 .env 文件，填入你的API密钥

    2. 启动Jupyter：
       jupyter lab

    3. 开始学习：
       打开 notebooks/ 目录查看教程notebooks
    """)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)