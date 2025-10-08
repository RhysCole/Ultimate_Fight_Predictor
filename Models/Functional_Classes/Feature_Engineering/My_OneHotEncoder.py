import numpy as np
import pandas as pd

class MyOneHotEncoder():
    def __init__(self):
        self.category_map_ = None
        self.inverse_category_map_ = None
        self.feature_names_ = None

    def fit(self, X: pd.Series):
        unique_categories = sorted(X.unique())

        self.category_map_ = {category: i for i, category in enumerate(unique_categories)}
        self.inverse_category_map_ = {i: category for i, category in enumerate(unique_categories)}
        self.feature_names_ = [f"{X.name}_{category}" for category in unique_categories]

        return self
    
    def transform(self, X: pd.Series):

        if self.category_map_ is None:
            raise RuntimeError("Encoder has not been fitted yet. Call .fit() first.")

        n_samples = len(X)
        n_categories = len(self.category_map_)
        transformed_features = np.zeros((n_samples, n_categories), dtype=int)

        for i, category in enumerate(X):
            category_index = self.category_map_.get(category)
            
            if category_index is not None:
                transformed_features[i, category_index] = 1
                
        return pd.DataFrame(transformed_features, columns=self.feature_names_, index=X.index)
    
    def fit_transform(self, X: pd.Series):
        return self.fit(X).transform(X)
    
    def inverse_transform(self, X: pd.DataFrame):
        return X.idxmax(axis=1).map(self.inverse_category_map_)