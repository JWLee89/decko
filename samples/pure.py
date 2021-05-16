from src.decko import Decko


if __name__ == "__main__":
    dk = Decko(__name__, debug=True)

    item = []

    @dk.pure()
    def add(array, value):
        array.append(value)

    for i in range(10):
        add(item, i)


