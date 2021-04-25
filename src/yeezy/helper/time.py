
def lazy_initialization(func, time_dict):
    if func not in time_dict:
        time_dict[func] = {}
    time_dict = time_dict[func]

    # Initialize state variables
    time_dict['count'] = 0
    time_dict['accumulated_time'] = 0

