# Yeezy

A simple utility belt for Python developers. Yee ...

![yee.png](yee.png)

## Getting Started

Yeezy is a decorated-based module for debugging. 
It also provides useful decorators to speed up programming and provides utility 
function for easier decorator usage. Here is an example

```python
from yeezy import Yeezy

yee = Yeezy(__name__, debug = True)

@yee.time
def create_list(n = 1000000):
    return list(range(n))

# Returns statistics on time
yee.analyze()

```
