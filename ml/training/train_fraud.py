"""Run: python ml/training/train_fraud.py"""
import numpy as np, pickle, os, random
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import mlflow

ARTIFACTS_DIR = "ml/artifacts/fraud_model"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("fraud_detection")

FEATURE_NAMES = ["doc_hash_reuse","submission_speed_seconds","ip_reuse_count",
                  "field_mismatch_score","time_since_last_app_days","district_anomaly_score","hour_of_day","is_weekend"]


def generate_synthetic_data(n=2000):
    X, y = [], []
    for _ in range(n):
        is_fraud = random.random() < 0.15
        if is_fraud:
            X.append([random.choice([0,1,1]), random.uniform(5,30), random.randint(3,10),
                      random.uniform(0.4,1.0), random.uniform(0,3), random.uniform(0.5,1.0),
                      random.randint(0,23), random.randint(0,1)])
        else:
            X.append([0, random.uniform(60,600), random.randint(1,3),
                      random.uniform(0,0.3), random.uniform(7,60), random.uniform(0,0.3),
                      random.randint(8,18), 0])
        y.append(int(is_fraud))
    return np.array(X, dtype=float), np.array(y)


def main():
    print("Generating synthetic fraud data...")
    X, y = generate_synthetic_data(2000)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    with mlflow.start_run(run_name="fraud_v1"):
        xgb_model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05,
            scale_pos_weight=6, eval_metric="auc", random_state=42, verbosity=0)
        xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        auc = roc_auc_score(y_val, xgb_model.predict_proba(X_val)[:,1])
        mlflow.log_metric("auc_roc", auc)
        iso = IsolationForest(contamination=0.15, random_state=42)
        iso.fit(X_train)
        out = f"{ARTIFACTS_DIR}/fraud_models.pkl"
        with open(out, "wb") as f:
            pickle.dump({"xgb_model": xgb_model, "iso_forest": iso, "feature_names": FEATURE_NAMES}, f)
        mlflow.log_artifact(out)
        print(f"Done. AUC-ROC={auc:.4f}")


if __name__ == "__main__":
    main()
