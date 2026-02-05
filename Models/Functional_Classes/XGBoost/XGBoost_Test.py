import unittest
import numpy as np
from Models.Functional_Classes.globals.TreeNode import TreeNode
from Models.Functional_Classes.XGBoost.My_XGBoost import My_XGBoost_Regressor
class TestXGBoostFull(unittest.TestCase):

    def setUp(self):
        self.X = np.array([[1], [2], [3], [4], [5]])
        self.y = np.array([2, 4, 6, 8, 10])
        self.model = My_XGBoost_Regressor(n_estimators=10, max_depth=2, reg_lambda=1.0)

    def test_leaf_value_math(self):
        gradients = np.array([-2.0, -2.0])
        hessians = np.array([1.0, 1.0])
        expected_val = 1.3333
        calculated_val = self.model.calc_best_leaf_value(gradients, hessians)
        self.assertAlmostEqual(calculated_val, expected_val, places=4)

    def test_split_logic(self):
        X = np.array([[1], [10]])
        gradients = np.array([-5.0, 5.0]) 
        hessians = np.array([1.0, 1.0])
        tree = self.model.build_tree(X, gradients, hessians, depth=0)
        self.assertFalse(tree.is_leaf())
        self.assertEqual(tree.split_threshold, 1)

    def test_model_learns(self):
        self.model.fit(self.X, self.y)
        preds = self.model.predict(self.X)
        baseline_mse = np.mean((self.y - np.mean(self.y)) ** 2)
        model_mse = np.mean((self.y - preds) ** 2)
        self.assertLess(model_mse, baseline_mse)

    def test_single_sample(self):
        X = np.array([[100]])
        y = np.array([50])
        try:
            self.model.fit(X, y)
            pred = self.model.predict(X)
        except Exception as e:
            self.fail(f"{e}")
        self.assertTrue(np.isfinite(pred[0]))

    def test_constant_target(self):
        X = np.array([[1], [2], [3]])
        y = np.array([10.0, 10.0, 10.0])
        self.model.fit(X, y)
        preds = self.model.predict(X)
        np.testing.assert_allclose(preds, y, atol=0.01)

    def test_massive_outlier(self):
        X = np.array([[1], [2], [3], [4]])
        y = np.array([1.0, 1.0, 1.0, 1000000.0])
        self.model.fit(X, y)
        preds = self.model.predict(X)
        self.assertGreater(preds[3], preds[0])

if __name__ == '__main__':
    unittest.main()