from collections import Counter

def most_common_label(y):
    counter = Counter(y)

    if not counter:
        return None
    
    return counter.most_common(1)[0][0]