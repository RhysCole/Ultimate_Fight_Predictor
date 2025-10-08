import numpy as np
import pandas as pd
from Models.Functional_Classes.TreeNode import TreeNode

class My_XGBoost_Regressor():
    def __init__(self, n_estimators=100, max_depth=3, learning_rate=0.1, gamma = 0.1, reg_lambda = 0.1, min_sample_split = 2):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth

        self.gamma = gamma
        self.reg_lambda = reg_lambda

        self.min_sample_split = min_sample_split

        self.trees = []
        self.base_prediction = None
        self.feature_importances = {}

    def fit(self, X: np.ndarray, y: np.ndarray):    
        if isinstance(X, pd.DataFrame):
            self.feature_importances = {col: 0 for col in X.columns}
            X = X.values

        self.base_prediction = np.mean(y)
        current_prediction = np.full(y.shape, self.base_prediction)

        for _ in range(self.n_estimators):
            gradients = 2 * (current_prediction - y)
            hessians = np.full(y.shape, 2)

            tree = self.build_tree(X, gradients, hessians, depth=0)
            self.trees.append(tree)

            updated_values = self.get_tree_predictions(tree, X)
            current_prediction += self.learning_rate * updated_values

    def build_tree(self, X, gradients, hessians, depth):
        n_samples, n_features = X.shape

        if depth >= self.max_depth or n_samples < self.min_sample_split:
            leaf_value = self.calc_best_leaf_value(gradients, hessians)
            return TreeNode(value = leaf_value)
        
        best_gain = -np.inf
        best_split_info = {}

        parent_g_sum = np.sum(gradients)
        parent_h_sum = np.sum(hessians)
        parent_quality = self.calc_quality(parent_g_sum, parent_h_sum)

        for feature_idx in range(n_features):

            for threshold in np.unique(X[: , feature_idx]):
                left_mask = X[:, feature_idx] <= threshold
                right_mask = ~left_mask

                if np.sum(left_mask) < 1 or np.sum(right_mask) < 1:
                    continue

                g_left, h_left = gradients[left_mask], hessians[left_mask]
                g_right, h_right = gradients[right_mask], hessians[right_mask]

                left_quality = self.calc_quality(np.sum(g_left), np.sum(h_left))
                right_quality =  self.calc_quality(np.sum(g_right), np.sum(h_right))

                gain = left_quality + right_quality - parent_quality - self.gamma

                if gain > best_gain:
                    best_gain = gain
                    best_split_info = {
                        "feature_idx": feature_idx,
                        "threshold": threshold,
                        "left_mask": left_mask,
                        "right_mask": right_mask,
                    }

        if best_gain <= self.gamma:
            leaf_value = self.calc_best_leaf_value(gradients, hessians)
            return TreeNode(value = leaf_value)
        
        if self.feature_importances:
            feature_name_index = best_split_info["feature_idx"]
            feature_name = list(self.feature_importances.keys())[feature_name_index]
            self.feature_importances[feature_name] += best_gain

        
        left_child = self.build_tree(
            X[best_split_info["left_mask"]],
            gradients[best_split_info["left_mask"]],
            hessians[best_split_info["left_mask"]],
            depth + 1
            )
        right_child = self.build_tree(
            X[best_split_info["right_mask"]],
            gradients[best_split_info["right_mask"]],
            hessians[best_split_info["right_mask"]],
            depth + 1
            )
        
        return TreeNode(
            split_feature_idx=best_split_info["feature_idx"],
            split_threshold=best_split_info["threshold"],
            left_child = left_child,
            right_child = right_child
            )
    
    def calc_best_leaf_value(self, gradients, hessians):
        return -np.sum(gradients) / (np.sum(hessians) + self.reg_lambda)


    def calc_quality(self, g_sum, h_sum):
        return (g_sum**2) / (h_sum + self.reg_lambda)

    def predict(self, X: np.ndarray):
        if isinstance(X, pd.DataFrame):
            X = X.values

        predictions = np.full((X.shape[0],), self.base_prediction)

        for tree in self.trees:
            predictions += self.learning_rate * self.get_tree_predictions(tree, X)

        return predictions

    def get_tree_predictions(self, tree, X):
        predictions = np.zeros(X.shape[0])

        for i , sample in enumerate(X):
            node = tree
            while not node.is_leaf():
                if sample[node.split_feature_idx] <= node.split_threshold:
                    node = node.left_child
                else:
                    node = node.right_child
            predictions[i] = node.value

        return predictions
    
