import time


def measure_execution_time(function):
    def wrapper(*args, **kwargs):
        # Record the start time
        start_time = time.time()

        # Execute the function
        result = function(*args, **kwargs)

        # Record the end time
        end_time = time.time()

        # Calculate the execution time
        execution_time = end_time - start_time

        # Display the execution time
        print(f"The function {function.__name__} took {execution_time:.4f} seconds to execute.")

        # Return the function's result
        return result

    return wrapper
