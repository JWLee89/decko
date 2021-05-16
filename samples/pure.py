from src.decko import Decko


if __name__ == "__main__":
    dk = Decko(__name__, debug=True)

    def raise_error(*args, **kwargs):
        print("yee")
        raise ValueError(f"Modified inputs: {args}, {kwargs}")


    @dk.pure()
    def input_output_what_how(a, b, c=[]):
        c.append(10)
        return c


    item = []
    yee = input_output_what_how(10, 20, item)
    print(item)

