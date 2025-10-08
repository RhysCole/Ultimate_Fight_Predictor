import os

current_dir = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, '..'))

DB_PATH = os.path.join(PROJECT_ROOT, "Database", "fighters.db")
MODEL_DIR = os.path.join(PROJECT_ROOT, "Models")

ENCODERS_PATH = os.path.join(PROJECT_ROOT, 'Models', 'Functional_Classes', 'logistic_regression', 'style_encoder.pkl')
DOMINANCE_ENCODER_PATH = os.path.join(PROJECT_ROOT, 'Elo_System', 'dominance_encoder.pkl')
COLUMNS_PATH = os.path.join(PROJECT_ROOT, 'Models', 'Functional_Classes', 'logistic_regression', 'style_model_columns.pkl')
MODEL_PATH = os.path.join(PROJECT_ROOT, 'Models', 'Functional_Classes', 'logistic_regression', 'style_model.pkl')
DOMINANCE_MODEL_PATH = os.path.join(PROJECT_ROOT, 'Elo_System', 'Performance_Vector_Modal', 'dominance_modal.pkl')
PREDICTOR_MODEL_PATH = os.path.join(PROJECT_ROOT, 'Fight_Predictor', 'bushy_model.pkl')
TEST_DATA_PATH = os.path.join(PROJECT_ROOT, 'Fight_Predictor', 'data', 'test_data.pkl')
