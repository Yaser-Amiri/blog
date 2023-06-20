Title: Respect __init__ to reduce your memory usage
Date: 2023-06-20
Category: python

Recently I was playing with some data using my beloved Python, and during transforming the records I found out
that CPython can optimize the memory usage of created objects of the same class in a very interesting way.  

I think most Python developers are familiar with `__slots__`, we mostly use it to reduce the memory usage of objects,
(it also can decrease attribute access time a bit) but it's full of caveats, especially when it gets mixed up with inheritance.
One limitation that `__slots__` brings to the table is the fact that you won't be able to add more attributes to the object
dynamically. Yes, adding instance attributes in that way is not neat and certainly can lead to weird bugs, although it can't be
that harmful if you're just trying to explore or play with some data in your Python shell, it's actually very nice!
Thereby I don't use `__slots__` in this kind of scenario and just write a simple class.

But does it mean that there is no other thing that we can do about object memory usage?  
No!  
![There is another]({static}/images/there-is-another.jpg "There is another")

**CPython (since 3.3) can share keys of `__dict__`** ([PEP 412 – Key-Sharing Dictionary](https://peps.python.org/pep-0412/))  
All the objects which we make of regular classes have a property named `__dict__`, it's a dictionary that basically holds
instance's attributes within, although there are many exceptions, using `__slots__` is one of them (It's possible to use them both
together but that would make more trouble than it fixes), using other custom descriptors can also bypass it.
Anyway, you can imagine if we create a million instances of a class with 10 attributes, we are actually making a million dictionaries,
it means 10 million keys are going to live in the memory separately, right?! Well, this is where PEP 412 comes to help.  

PEP 412 basically says CPython can optimize these dicts and use the same keys and hashes as long as you don't change the keys.
It will help you if you keep your keys (instance attributes) constant and don't add more attributes after initialization.

Let's do an experiment and see how it works.  
``` python
from pympler.asizeof import asizeof

class Foo:
    def __init__(self, a, b, c, d, e, f, g):
        self.aaaaa = a
        self.bbbbb = b
        self.ccccc = c
        self.ddddd = d
        self.eeeee = e
        self.fffff = f
        self.ggggg = g


f1 = Foo(0, 0, 0, 0, 0, 0, 0)
f1.y = 9

data = []
for i in range(10000):
    obj = Foo(i, i, i, i, i, i, i)
    obj.z = 1
    data.append(obj)

print("Size of the list:", asizeof(data) / 1000, "KB")
```

We have a simple class named `Foo` we create an instance named `f1` and add a new attribute `y`, then we make 10000 other instances and add
a new attribute named `z` dynamically. Result of the code: `Size of the list: 4485.896 KB`  

Now let's make it static and create all the attributes we need at the `__init__`:

``` python
from pympler.asizeof import asizeof

class Foo:
    def __init__(self, a, b, c, d, e, f, g):
        self.aaaaa = a
        self.bbbbb = b
        self.ccccc = c
        self.ddddd = d
        self.eeeee = e
        self.fffff = f
        self.ggggg = g
        self.y = None
        self.z = None


f1 = Foo(0, 0, 0, 0, 0, 0, 0)
f1.y = 9

data = []
for i in range(10000):
    obj = Foo(i, i, i, i, i, i, i)
    obj.z = 1
    data.append(obj)

print("Size of the list:", asizeof(data) / 1000, "KB")
```

Result: `Size of the list: 2325.56 KB`, almost 50% percent better! Isn't that great?! In this case, we don't add any new attributes,
which means we let CPython use the same data(hashes and keys) for the new dictionaries. It just creates a new data structure for dict values.  
I love it this way, with a simple change in my class I can load more data on memory to play with, and don't have to deal with `__slots__`.

**Note: __slots__ is still much more efficient.**
