import numpy as np
import pandas as pd

class MyLogisticRegressor():
    def __init__(self, learning_rate=0.01, n_iterations=100):
        self.learning_rate = learning_rate
        self.iterations = n_iterations

        self.weights = None
        self.bias = None

    def sigmoid(self, z):
        z = np.clip(z, -250,250)
        return 1/(1+np.exp(-z))

    def fit(self, X, y):
        n_samples, n_features = X.shape

        self.weights = np.zeros(n_features)
        self.bias = 0

        for _ in range(self.iterations):
            model_output = np.dot(X, self.weights) + self.bias
            y_prediction = self.sigmoid(model_output)

            direction_weight = (1 / n_samples) * np.dot(X.T, (y_prediction - y))
            direction_bias = (1 / n_samples) * np.sum(y_prediction - y)

            self.weights -= self.learning_rate * direction_weight
            self.bias -= self.learning_rate * direction_bias

    def predict(self, X, threshold=0.5):
        probabilities = self.predict_proba(X)
        return ( probabilities > threshold).astype(int)

    def predict_proba(self, X):
        model_output = np.dot(X, self.weights) + self.bias
        return self.sigmoid(model_output)

