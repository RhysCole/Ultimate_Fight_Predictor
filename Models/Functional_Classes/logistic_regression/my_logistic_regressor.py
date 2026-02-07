import numpy as np
import pandas as pd

class MyLogisticRegressor():
    def __init__(self, learning_rate=0.01, n_iterations=100):
        # Initialize hyperparameters for gradient descent
        self.learning_rate = learning_rate
        self.iterations = n_iterations

        self.weights = None
        self.bias = None

    def sigmoid(self, z):
        # Clip input to prevent overflow or underflow error in exp()
        z = np.clip(z, -250, 250)
        # Apply sigmoid  function to map values beteween [0, 1]
        return 1/(1+np.exp(-z))

    def fit(self, X, y):
        n_samples, n_features = X.shape

        # Initialize weights as zeros and bias as scalar zero
        self.weights = np.zeros(n_features)
        self.bias = 0

        for _ in range(self.iterations):
            # Calculate linear prediction 
            model_output = np.dot(X, self.weights) + self.bias
            y_prediction = self.sigmoid(model_output)

            # Calculate gradients for weights and bias
            direction_weight = (1 / n_samples) * np.dot(X.T, (y_prediction - y))
            direction_bias = (1 / n_samples) * np.sum(y_prediction - y)

            # Update parameters by moving against the gradient
            self.weights -= self.learning_rate * direction_weight
            self.bias -= self.learning_rate * direction_bias

    def predict(self, X, threshold=0.5):
        # Convert probabilities to binary labels
        probabilities = self.predict_proba(X)
        return (probabilities > threshold).astype(int)

    def predict_proba(self, X):
        # Return raw probability scores 
        model_output = np.dot(X, self.weights) + self.bias
        return self.sigmoid(model_output)