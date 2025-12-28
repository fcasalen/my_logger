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
# Or use as a decorator in both synchronous and asynchronous functions
@logger.log_exception_decorator()
def your_function():
    # Your code here
    pass

# using re_raise to propagate the exception after logging
@logger.log_exception_decorator(re_raise=True)
def your_function():
    # Your code here
    pass

@logger.log_exception_decorator()
async def your_async_function():
    # Your code here
    pass
```

## Requirements

- Python >= 3.11, <4.0
- loguru >= 0.7.3, <1.0.0
