from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "ev_battery_test_data (1).xlsx"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

BATTERY_FEATURES = ["voltage_V", "current_A", "battery_temp_C"]
BATTERY_ENV_FEATURES = [
    "voltage_V",
    "current_A",
    "battery_temp_C",
    "ambient_temp_C",
    "humidity_pct",
]
TARGET_COLUMN = "fault_label"


def load_dataset() -> pd.DataFrame:
    df = pd.read_excel(DATASET_PATH, sheet_name="Data")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset. Available columns: {list(df.columns)}")

    missing = [feature for feature in BATTERY_ENV_FEATURES if feature not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")

    df = df.copy()
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)
    return df


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
    }
    return metrics


def train_model_for_features(feature_names: list[str], model_name: str) -> dict:
    df = load_dataset()
    X = df[feature_names]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", DecisionTreeClassifier(random_state=42, max_depth=5)),
        ]
    )
    model.fit(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)

    MODELS_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODELS_DIR / f"{model_name}.pkl")

    return {
        "model_name": model_name,
        "features": feature_names,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "metrics": metrics,
    }


def train_and_save_models() -> dict:
    model_a = train_model_for_features(BATTERY_FEATURES, "model_a")
    model_b = train_model_for_features(BATTERY_ENV_FEATURES, "model_b")

    results = {
        "dataset_file": DATASET_PATH.name,
        "target_column": TARGET_COLUMN,
        "feature_order": {
            "model_a": BATTERY_FEATURES,
            "model_b": BATTERY_ENV_FEATURES,
        },
        "comparison": [
            {"model": "Model A (battery only)", **model_a["metrics"]},
            {"model": "Model B (battery + environment)", **model_b["metrics"]},
        ],
    }

    with (OUTPUTS_DIR / "model_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Training results:\n")
    for model_result in results["comparison"]:
        print(model_result["model"])
        print("  accuracy:", model_result["accuracy"])
        print("  precision:", model_result["precision"])
        print("  recall:", model_result["recall"])
        print("  f1_score:", model_result["f1_score"])
        print("  confusion_matrix:", model_result["confusion_matrix"])

    return results


if __name__ == "__main__":
    train_and_save_models()
