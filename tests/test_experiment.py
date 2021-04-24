from src.yeezy.helper.util import TimeComputer


def test_time_computer_outputs_float():
    """
    Check to see if the TimeComputer() outputs a float value.
    :return: None
    """
    time_taken = []
    for i in range(100):
        with TimeComputer(time_taken):
            dummy_list = list(range(10000))
    mean_time_ms = TimeComputer.compute_avg_time(time_taken, TimeComputer.Units.MS)
    assert isinstance(mean_time_ms, float)

