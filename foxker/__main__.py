"""
Foxker 包入口点
支持 python -m foxker 运行
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
