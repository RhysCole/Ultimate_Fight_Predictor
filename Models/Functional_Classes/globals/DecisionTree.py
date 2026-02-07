import numpy as np
import pandas as pd

from Models.Functional_Classes.globals.TreeNode import TreeNode
from Models.Functional_Classes.globals.Most_Common_lable import most_common_label

class DecisionTree:
    def __init__(self, max_depth = 10, min_samples_split = 2, n_features = None):
        # Initialize hyperparameters
        self.max_depth = max_depth
        self.n_features = n_features
        self.min_samples_split = min_samples_split
        self.root = None
        
    def fit(self, X, y):
        # Determine number of features to consider 
        self.n_features = X.shape[1] if not self.n_features else min(X.shape[1], self.n_features)
        # Start the recursive tree building process from the root
        self.root = self.build_tree(X, y)
        
    def build_tree(self, X, y, depth=0):
        n_samples, n_features = X.shape
        n_labels = len(np.unique(y))
        
        # Base cases: Stop recursion if max depth reached, node is pure, or too few samples
        if (depth >= self.max_depth or n_labels == 1 or n_samples < self.min_samples_split):
            leaf_value = most_common_label(y)
            if leaf_value is None:
                # Debugging print for edge case where label finding fails
                print('first bit set a none', 'y: ', y, 'depth:', depth >= self.max_depth)
            return TreeNode(value=leaf_value)

        # Randomly select a subset of features to evaluate for splitting
        feat_idxs = np.random.choice(n_features, self.n_features, replace=False)

        # Find the best feature and threshold to split this node
        best_feat, best_thresh = self.find_best_split(X, y, feat_idxs)
        
        # If no valid split is found, return a leaf node
        if best_feat is None or best_thresh is None:
            leaf_value = most_common_label(y)
            if leaf_value is None:
                print('second bit set a none')
            return TreeNode(value=leaf_value)

        # Perform the split
        left_idxs, right_idxs = self.split(X[:, best_feat], best_thresh)
        
        # If a split results in an empty child, stop and return a leaf
        if len(left_idxs) == 0 or len(right_idxs) == 0:
            leaf_value = most_common_label(y)
            return TreeNode(value=leaf_value)
        
        # Recursively build the left and right child nodes
        left_child = self.build_tree(X[left_idxs, :], y[left_idxs], depth + 1)
        right_child = self.build_tree(X[right_idxs, :], y[right_idxs], depth + 1)
                
        return TreeNode(split_feature_idx=best_feat, split_threshold=best_thresh, left_child=left_child, right_child=right_child)
        
    def find_best_split(self, X, y, feature_idxs):
        best_gain = -np.inf
        split_idx, split_threshold = None, None
        
        # Iterate through selected features and their unique values to find max information gain
        for feature_idx in feature_idxs:
            X_col = X[:, feature_idx]
            thresholds = np.unique(X_col)
            
            for threshold in thresholds:
                gain = self.information_gain(y, X_col, threshold)
                
                if gain > best_gain:
                    best_gain = gain
                    split_idx = feature_idx
                    split_threshold = threshold
        
        if split_idx is None or split_threshold is None:
            return None, None
    
        return split_idx, split_threshold
    
    def information_gain(self, y, X, threshold):
        # Calculate parent impurity (Gini)
        parent_gini = self.gini(y)
        
        left_idxs, right_idxs = self.split(X, threshold)
        
        if len(left_idxs) == 0 or len(right_idxs) == 0:
            return 0
        
        # Calculate weighted average impurity of children
        n = len(y)
        n_left, n_right = len(left_idxs), len(right_idxs)
        gini_left, gini_right = self.gini(y[left_idxs]), self.gini(y[right_idxs])
        
        child_gini = (n_left / n) * gini_left + (n_right / n) * gini_right
        
        # Information Gain = Parent Impurity - Weighted Child Impurity
        return parent_gini - child_gini
    
    def split(self, X_col, split_threshold):
        # Get indices for samples that go left (<= threshold) vs right (> threshold)
        left_idxs = np.argwhere(X_col <= split_threshold).flatten()
        right_idxs = np.argwhere(X_col > split_threshold).flatten()
        
        return left_idxs, right_idxs
    
    def gini(self, y):
        try:
            # Count occurrences of each class label
            hist = np.bincount(y)
        except Exception as e:
            print(f"np.bincount failed on y={y}")
            raise 
        
        # Calculate probabilities and sum of squared probabilities
        ps = hist / len(y)
        return 1 - np.sum([p**2 for p in ps if p > 0])
    
    
    def predict(self, X):
        # Predict class for every sample in X
        return np.array([self.traverse_tree(x ,self.root) for x in X])
    
    def traverse_tree(self, x, node, parent=None):
        # Recursive function to traverse down to a leaf
        if node.is_leaf():
            return node.value
        
        # Decide which child to visit based on feature threshold
        if x[node.split_feature_idx] <= node.split_threshold:
            return self.traverse_tree(x, node.left_child, parent = node)
                
        return self.traverse_tree(x, node.right_child, parent=node)
    
    def debug_tree(self, node=None, depth=0):
        # Recursively print tree structure for debugging
        none_count = 0
        
        if node is None:
            node = self.root

        indent = "  " * depth
        if node.split_feature_idx is not None:
            print(f"{indent}Feature {node.split_feature_idx} <= {node.split_threshold}")
            if node.left_child:
                self.debug_tree(node.left_child, depth + 1)
            if node.right_child:
                self.debug_tree(node.right_child, depth + 1)
        else:
            if node.value is None:
                none_count += 1
                
            print(f"{indent}Leaf: value={node.value}")
            
        return(none_count)