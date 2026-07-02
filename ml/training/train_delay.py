"""Run: python ml/training/train_delay.py"""
import numpy as np, pickle, os, random
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import mlflow

ARTIFACTS_DIR = "ml/artifacts/delay_model"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("delay_prediction")

CERT_MAP = {"caste_certificate":0,"birth_certificate":1,"income_certificate":2,"domicile_certificate":3,"death_certificate":4}
BASE_DELAYS = [7,5,6,8,4]


def generate_data(n=1000):
    X, y = [], []
    for _ in range(n):
        cert = random.randint(0,4)
        officer_load = random.randint(5,30)
        backlog = random.randint(5,50)
        month = random.randint(1,12)
        weekday = random.randint(0,6)
        festival = 1 if month in [10,11,3,4] else 0
        base = BASE_DELAYS[cert]
        delay = base * (1 + (officer_load-10)*0.05) * (1.3 if festival else 1.0) * (1.2 if backlog > 30 else 1.0)
        delay += random.uniform(-1, 2)
        X.append([cert, officer_load, backlog, month, weekday, festival])
        y.append(max(1.0, delay))
    return np.array(X, dtype=float), np.array(y)


def main():
    X, y = generate_data(1000)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    with mlflow.start_run(run_name="delay_v1"):
        model = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42, verbosity=0)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        mae = mean_absolute_error(y_val, model.predict(X_val))
        mlflow.log_metric("mae", mae)
        out = f"{ARTIFACTS_DIR}/delay_models.pkl"
        with open(out, "wb") as f:
            pickle.dump({"xgb_model": model}, f)
        mlflow.log_artifact(out)
        print(f"Done. MAE={mae:.4f} days")


if __name__ == "__main__":
    main()
