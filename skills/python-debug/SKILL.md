---
name: python-debug
description: Debug Python code using pdb and logging
tags: python, debug
---
# Python Debugging Guide

## Using pdb

Insert breakpoints:
```python
import pdb; pdb.set_trace()
```

Common pdb commands:
- `n` - next line
- `s` - step into
- `c` - continue
- `p <var>` - print variable
- `l` - list source
- `q` - quit

## Using logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message: %s", variable)
```
