"""
Run: python ml/training/train_complaint.py
Trains mBERT + LightGBM complaint classifier.
"""
import json, os, pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, mean_absolute_error
import lightgbm as lgb
import mlflow

DATA_PATH = "ml/data/processed/complaints.json"
ARTIFACTS_DIR = "ml/artifacts/complaint_model"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("complaint_classifier")

DEPT_MAP = {
    "officer_misconduct": "Vigilance Department", "urgent_grievance": "Collector Office",
    "portal_technical": "IT Department", "wrong_information": "Revenue Department",
    "document_rejection": "Revenue Department", "certificate_delay": "Revenue Department",
    "scheme_information": "Welfare Department",
}


def get_embeddings(texts):
    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
        model = AutoModel.from_pretrained("bert-base-multilingual-cased")
        model.eval()
        embeddings = []
        for i in range(0, len(texts), 16):
            batch = texts[i:i+16]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**encoded)
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            pooled = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1)
            embeddings.append(pooled.numpy())
            if i % 80 == 0: print(f"  Embedded {min(i+16, len(texts))}/{len(texts)}")
        return np.vstack(embeddings)
    except ImportError:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=768, ngram_range=(1, 2))
        emb = vec.fit_transform(texts).toarray()
        with open(f"{ARTIFACTS_DIR}/tfidf_vectorizer.pkl", "wb") as f:
            pickle.dump(vec, f)
        return emb


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    texts = [d["text"] for d in data]
    categories = [d["category"] for d in data]
    urgencies = [d["urgency_score"] for d in data]
    label_enc = LabelEncoder()
    y_cat = label_enc.fit_transform(categories)
    y_urg = np.array(urgencies)
    X_train_t, X_val_t, y_ct, y_cv, y_ut, y_uv = train_test_split(
        texts, y_cat, y_urg, test_size=0.2, random_state=42, stratify=y_cat)
    print("Generating embeddings...")
    X_train, X_val = get_embeddings(X_train_t), get_embeddings(X_val_t)
    with mlflow.start_run(run_name="complaint_v1"):
        cat_model = lgb.LGBMClassifier(num_class=len(set(y_cat)), objective="multiclass",
            learning_rate=0.05, num_leaves=31, n_estimators=200, random_state=42, verbose=-1)
        cat_model.fit(X_train, y_ct, eval_set=[(X_val, y_cv)], callbacks=[lgb.early_stopping(20), lgb.log_evaluation(50)])
        f1 = f1_score(y_cv, cat_model.predict(X_val), average="macro")
        mlflow.log_metric("category_f1_macro", f1)

        urg_model = lgb.LGBMRegressor(objective="regression", learning_rate=0.05, n_estimators=150, random_state=42, verbose=-1)
        urg_model.fit(X_train, y_ut, eval_set=[(X_val, y_uv)], callbacks=[lgb.early_stopping(20), lgb.log_evaluation(50)])
        mae = mean_absolute_error(y_uv, urg_model.predict(X_val))
        mlflow.log_metric("urgency_mae", mae)

        dept_map = {}
        for cat in label_enc.classes_:
            dept_map[cat] = DEPT_MAP.get(cat, "Revenue Department")

        artifacts = {"category_model": cat_model, "urgency_model": urg_model,
                     "label_encoder": label_enc, "categories": list(label_enc.classes_), "department_map": dept_map}
        out = f"{ARTIFACTS_DIR}/complaint_models.pkl"
        with open(out, "wb") as f:
            pickle.dump(artifacts, f)
        mlflow.log_artifact(out)
        print(f"Done. F1={f1:.4f} MAE={mae:.4f}")


if __name__ == "__main__":
    main()
