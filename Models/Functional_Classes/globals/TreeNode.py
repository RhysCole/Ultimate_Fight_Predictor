

class TreeNode: 
    def __init__(self, left_child=None, right_child=None, split_feature_idx=None, split_threshold=None, *, value=None, parent = None):
        
        self.value = value
        self.left_child = left_child
        self.right_child = right_child
        self.split_feature_idx = split_feature_idx
        self.split_threshold = split_threshold
        self.parent = parent

    def is_leaf(self):
        return self.value is not None
    
    def __repr__ (self):
        return(f"value: {self.value} split_feature_idx: {self.split_feature_idx} split_threshold: {self.split_threshold} left_child: {self.left_child} right_child: {self.right_child} isleaf:{self.is_leaf()}")
