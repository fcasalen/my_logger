# My Logger

A custom logger implementation using loguru for exception handling.

## Features

- Logs one exception per file with unique UUID
- Creates logs in specified folder's `logs` subfolder
- Automatically skips logging during pytest execution
- Custom exception messages support

## Installation

```bash
pip install my_logger
```

## Usage

```python
from pathlib import Path
from my_logger import MyLogger

logger = MyLogger(Path("your/project/folder"))

try:
    # Your code here
    pass
except Exception:
    logger.log_exception("Something went wrong!")
```

## Requirements

- Python >= 3.11, <4.0
- loguru >= 0.7.3, <1.0.0