"""Test immediate single use pattern - should be flagged."""


def example1():
    # Should flag: literal assigned and used immediately
    x = "foo"
    func(x=x)


def example2():
    # Should flag: simple value assigned and returned immediately
    result = get_value()
    return result


def example3():
    # Should flag: literal in function call
    name = "Alice"
    greet(name)
