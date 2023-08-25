Title: Python's Data Containers Comparison
Date: 2023-08-24
Category: python

With Python 3.7 data classes have been introduced. They are simple classes that can hold some data as attributes,
support type hints in a clean way, and provide a default constructor for developers. Good news! they can be immutable (frozen).
I know the `dataclasses` lib provides much more features but what I described below, covers most of my use cases and is good enough.
Now I want to compare it with the older options and methods that we can use to hold data and access
them by attribute like named tuples or even better NamedTuple from `typing` and
of course a simple Python class with an `__init__`.

_Note: I use CPython 3.10.11_

### What I need
This is what I want in terms of interface:  
``` python
>>> yaser = Person(name="Yaser", age=26)
>>> print(yaser.age)
26
```

__Also I need it to be compatible with mypy.__


### Class Implementations

I'll go for these:

- Simple Python classes with `__init__`
- Simple Python classes in combination with slots
- Named tuples (from `typing` lib)
- Data classes (from `dataclasses` lib)
- Frozen data classes (We like immutability after all!)



``` python

from typing import NamedTuple
from dataclasses import dataclass


class NamedTuplePerson(NamedTuple):
    name: str
    age: int


@dataclass
class DataClassPerson:
    name: str
    age: int


@dataclass(frozen=True)
class FrozenDataClassPerson:
    name: str
    age: int


class RawClassPerson:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age


class SlotClassPerson:
    __slots__ = ("name", "age")

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age
```

Now all of these classes can be used for my use case, let's see how they're doing!

### Construction

Let's see how long it takes to instantiate these classes, this is the function that I'll run by `timeit`:

``` python
name, age = "a", 1

def test_construction(cls, size = 1000):
    collection = [None] * size
    for i in range(size):
        collection[i] = cls(name=name, age=age)
    return collection
```

Yes, I'm not just measuring the construction time, but I want to be sure about keeping multiple instances in the memory and their consequences.
And here's the result:  
```
NamedTuplePerson      => 5.113
DataClassPerson       => 5.347
FrozenDataClassPerson => 7.49
RawClassPerson        => 5.319
SlotClassPerson       => 4.514
```


### Memory usage

Now I'm gonna create a list of 100,000 instances and measure its size by `pympler.asizeof`:

``` python
def test_size(cls):
    # used test_construction from the previous test
    return int(asizeof(test_construction(cls, size=100000)) / 1000)
```

The result:  
```
NamedTuplePerson      => 6400 KB
DataClassPerson       => 16000 KB
FrozenDataClassPerson => 16000 KB
RawClassPerson        => 16000 KB
SlotClassPerson       => 5600 KB
```


### Conclusion
Well, classes that use slots are very efficient in instantiation time and RAM usage, but we know they are full of gotchas, and personally
I don't like to write my attributes as strings in `__slots__`.  
The second best option is using name tuple, which is close to slots and good enough!  
The other ones are the same in memory usage and slower but instantiation of frozen data classes is considerably slower!

Good luck.
