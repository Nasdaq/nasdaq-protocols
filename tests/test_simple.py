class Base:
    def __getattr__(self, item):
        print("Base.__getattr__")
        return 10


class Derived(Base):
    def __getattr__(self, item):
        print("Derived.__getattr__")
        return 20


def test_sample():
    d = Derived()
    print(d.x)