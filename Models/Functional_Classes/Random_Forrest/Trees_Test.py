import unittest
import numpy as np

# Adjust these imports to match your actual file structure
from Models.Functional_Classes.globals.DecisionTree import DecisionTree
from Models.Functional_Classes.globals.My_Random_Forrest import My_Random_Forrest

class TestTreeModels(unittest.TestCase):

    def setUp(self):
        self.X_xor = np.array([[0,0], [1,1], [0,1], [1,0]])
        self.y_xor = np.array([0, 0, 1, 1])

    # DECISION TREE TESTS

    def test_dt_perfect_split_normal(self):
        X = np.array([[0], [1], [10], [11]])
        y = np.array([0, 0, 1, 1])
        
        tree = DecisionTree(max_depth=5)
        tree.fit(X, y)
        preds = tree.predict(X)
        
        np.testing.assert_array_equal(preds, y, "Tree failed to separate obvious clusters.")

    def test_dt_pure_node_extreme(self):
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 1, 1]) # All same
        
        tree = DecisionTree()
        tree.fit(X, y)
        
        self.assertTrue(tree.root.is_leaf(), "Tree tried to split a pure node (waste of compute).")
        self.assertEqual(tree.root.value, 1, "Leaf value should be the only class available (1).")

    def test_dt_single_sample_extreme(self):
        X = np.array([[50, 50]])
        y = np.array([0])
        
        tree = DecisionTree(min_samples_split=2)
        try:
            tree.fit(X, y)
            pred = tree.predict(X)
        except Exception as e:
            self.fail(f"Tree crashed on single sample: {e}")
            
        self.assertEqual(pred[0], 0, "Prediction for single sample was wrong.")

    # RANDOM FOREST TESTS

    def test_rf_integration_normal(self):
        rf = My_Random_Forrest(n_estimators=5, max_depth=3)
        rf.fit(self.X_xor, self.y_xor)
        preds = rf.predict(self.X_xor)
        
        self.assertEqual(preds.shape, self.y_xor.shape, "RF output shape mismatch.")

    def test_rf_feature_subsampling(self):
        X = np.random.rand(10, 10)
        y = np.zeros(10, dtype=int)
        
        rf = My_Random_Forrest(n_estimators=2, n_features=1) 
        try:
            rf.fit(X, y)
        except Exception as e:
            self.fail(f"Random Forest crashed when using n_features subset: {e}")

if __name__ == '__main__':
    unittest.main()