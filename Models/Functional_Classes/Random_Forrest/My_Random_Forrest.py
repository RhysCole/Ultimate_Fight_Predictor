import numpy as np

from Models.Functional_Classes.globals.DecisionTree import DecisionTree
from Models.Functional_Classes.globals.Most_Common_lable import most_common_label

class My_Random_Forrest():
    def __init__(self, n_estimators = 100, max_depth = 10, min_samples_split = 2, n_features = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.n_features = n_features
        
        self.trees = []
        
    def fit(self, X, y,):
        self.trees = []
        
        for _ in range(self.n_estimators):
            X_sample, y_sample = self.bootstrap(X, y)
            
            tree = DecisionTree(
                max_depth = self.max_depth,
                min_samples_split=self.min_samples_split,
                n_features=self.n_features
            )
            
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)
                    
    def bootstrap(self, X, y):
        n_samples = X.shape[0]
        
        idxs = np.random.choice(n_samples, n_samples, replace=True)
        
        return X[idxs], y[idxs]
    
    def predict(self, X):
        predictions = np.array([tree.predict(X) for tree in self.trees])
        tree_preds = np.swapaxes(predictions, 0, 1)
        return np.array([most_common_label(tree_pred) for tree_pred in tree_preds])
