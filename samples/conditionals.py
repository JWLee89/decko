from src.decko import Decko
import numbers

dk = Decko(__name__)

if __name__ == "__main__":

    def is_number(name):
        return isinstance(name, numbers.Number)

    def handle(output, num):
         print("yeeeeeee")

    # TODO: Change fire if to accept a single function
    # The decorated function will fire if predicate is truthy value
    # Create dk.observe
    @dk.execute_if(is_number)
    def do_something(troll):
        print(f"Hello, i am a {troll}")

    do_something(100)
    do_something("100")

