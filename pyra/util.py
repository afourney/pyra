
def binary_search(sequence, item, start=0, end=None):
    """
    Returns the index of item in sequence if it exists,
    otherwise returns the index _would_ take if inserted.

    Searches between start (inclusive) and end (exclusive),
    which default to 0 and len(sequence) respectively.
    """ 

    if end is None:
        end = len(sequence)
    
    while start < end:
        mid = (start + end)//2

        if sequence[mid] > item:
            end = mid # Remember, end is exclsuive
        elif sequence[mid] < item:
            start = mid+1
        else: 
            return mid

    return start


def galloping_search(sequence, item, hint=0):
    """
    Returns the index of item in sequence if it exists,
    otherwise returns the index _would_ take if inserted.

    Searches between start (inclusive) and end (exclusive),
    which default to 0 and len(sequence) respectively.
    """ 

    if len(sequence) == 0:
        return 0

    if sequence[hint] < item:
        return _gsearch_forward(sequence, item, hint+1)
    elif sequence[hint] > item:
        return _gsearch_back(sequence, item, hint)
    else: 
        # It was a good hint
        return hint


def _gsearch_forward(sequence, item, low):

    # Gallop to find the range containing item
    jump = 1
    high = low + jump

    while high < len(sequence) and sequence[high-1] < item:
        low = high
        jump = 2 * jump
        high = low + jump

    # Binary search within the range
    return binary_search(sequence, item, max(0, low), min(high, len(sequence)))


def _gsearch_back(sequence, item, high):

    # Gallop to find the range containing item
    jump = 1
    low = high - jump

    while low >= 0 and sequence[low] > item:
        high = low
        jump = 2 * jump
        low = high - jump

    # Binary search within the range
    return binary_search(sequence, item, max(0, low), min(high, len(sequence)))
