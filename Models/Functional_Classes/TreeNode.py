class TreeNode: 
    def __init__(self, left_child=None, right_child=None, split_feature_idx=None, split_threshold=None, *, value=None):
        self.value = value
        self.left_child = left_child
        self.right_child = right_child
        self.split_feature_idx = split_feature_idx
        self.split_threshold = split_threshold

    def is_leaf(self):
        return self.value is not None
