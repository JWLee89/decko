# Pojang

A decorator based utility module for Python developers. The module is designed to 
aid developers in debugging their python applications.

![yee.png](yee.png)

## Getting Started

Pojang is a decorated-based module for debugging. 
It also provides useful decorators to speed up programming and provides utility 
function for easier decorator usage. Here is an example

```python
from pojang import Pojang

pj = Pojang(__name__, debug = True)

@pj.time
def create_list(n = 1000000):
    return list(range(n))

# Returns statistics on time
pj.analyze()

```
