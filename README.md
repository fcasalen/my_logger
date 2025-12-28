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
from my_logger import MyLogger, OptPrint

logger = MyLogger(Path("your/project/folder"))

try:
    # Your code here
    pass
except Exception:
    logger.log_exception("Something went wrong!")
# Or use as a decorator in both synchronous and asynchronous functions
# decorator has the same parameters as the log_exception method, plus the re_raise parameter
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

# to print the full path to the log file in the message
logger = MyLogger(Path("your/project/folder"), opt_print=OptPrint.FULL_PATH)

# to print the relative path to the log file in the message
logger = MyLogger(Path("your/project/folder"), opt_print=OptPrint.REL_PATH)

# to customize the standard message (if it has the placeholder {opt_print_adj},
# it will be replaced accordingly to the opt_print option)
logger = MyLogger(Path("your/project/folder"), std_msg="An error occurred! See log at {opt_print_adj}")

# if you want to add extra information to the log file, you can do it like this:
# the header_exc parameter will be added at the top of the log file
logger.log_exception(header_exc="User Data Processing Error")

# if you want to print a message only one time when logging an exception, you can do it like this:
logger.log_exception(one_time_message="This is a one-time message before logging the exception.")
```

## Requirements

- Python >= 3.11, <4.0
- loguru >= 0.7.3, <1.0.0
