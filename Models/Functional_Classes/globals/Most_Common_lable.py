from collections import Counter

# a function used to identify the most commen data lable in a given data set
def most_common_label(y):
    #return a dictionary with ranked label occurances and is ordered 
    counter = Counter(y)
    if not counter:
        return None
    
    return counter.most_common(1)[0][0]