import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, mean_squared_error, r2_score
from database import get_db
from models import Movie, Rating
from recommender import Recommender
from predict import RatingPredictor
from utils import extract_features

os.makedirs("eval", exist_ok=True)
db = next(get_db())
recommender = Recommender(db)
movies = db.query(Movie).all()
ratings = db.query(Rating).all()
mlb_genres = recommender.mlb_genres

rating_predictor = RatingPredictor(model_dir="models")
rating_predictor.load()

# Prepare data
X = []
y = []
for r in ratings:
    movie = next((m for m in movies if m.id == r.movie_id), None)
    if movie:
        X.append(extract_features(movie, mlb_genres))
        y.append(int(round(r.rating)))
X = np.array(X)
y = np.array(y)

# --- XGBoost Evaluation ---

# Predict with XGBoost
y_pred_xgb = rating_predictor.xgb.predict(rating_predictor.scaler.transform(X))
y_pred_xgb_rounded = np.clip(np.round(y_pred_xgb), 1, 10).astype(int)

# Classification report and confusion matrix for XGBoost
report_xgb = classification_report(y, y_pred_xgb_rounded, digits=4)
cm_xgb = confusion_matrix(y, y_pred_xgb_rounded, labels=range(1, 11))
acc_xgb = accuracy_score(y, y_pred_xgb_rounded)

# Save confusion matrix as image
plt.figure(figsize=(6, 5))
plt.imshow(cm_xgb, cmap='Blues')
plt.title(f'XGBoost Confusion Matrix\nAccuracy: {acc_xgb:.4f}')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.colorbar()
plt.tight_layout()
plt.savefig("eval/xgb_confusion_matrix.svg")
plt.close()

# Save classification report as text
with open("eval/xgb_classification_report.txt", "w") as f:
    f.write(report_xgb)

# --- XGBoost Regression Metrics ---
mse_xgb = mean_squared_error(y, y_pred_xgb)
r2_xgb = r2_score(y, y_pred_xgb)

with open("eval/xgb_regression_metrics.txt", "w") as f:
    f.write(f"Mean Squared Error (MSE): {mse_xgb:.4f}\n")
    f.write(f"R2 Score: {r2_xgb:.4f}\n")

# --- XGBoost Error Distribution ---
errors = y - y_pred_xgb
plt.figure(figsize=(8,4))
plt.hist(errors, bins=20, color='purple', alpha=0.7)
plt.xlabel("Eroare (rating real - rating prezis)")
plt.ylabel("Frecvență")
plt.title("Distribuția erorilor XGBoost")
plt.tight_layout()
plt.savefig("eval/xgb_error_distribution.svg")
plt.close()

# --- XGBoost Feature Importance ---
import xgboost as xgb

# Obține importanța și indexul
booster = rating_predictor.xgb.get_booster()
importance_dict = booster.get_score(importance_type='weight')

# Obține feature_names
_, feature_names = extract_features(movies[0], mlb_genres, return_names=True)

# Creează mapping index -> nume
mapped = {}
for fidx, score in importance_dict.items():
    idx = int(fidx.replace('f', ''))
    if idx < len(feature_names):
        mapped[feature_names[idx]] = score
    else:
        mapped[fidx] = score

# Sortează
sorted_items = sorted(mapped.items(), key=lambda x: float(x[1]), reverse=True)
names = [x[0] for x in sorted_items]
scores = [x[1] for x in sorted_items]

plt.figure(figsize=(8,6))
plt.barh(names, scores)
plt.xlabel("Importance score")
plt.title("Feature importance (XGBoost)")
plt.tight_layout()
plt.savefig("eval/xgb_feature_importance.svg")
plt.close()

# --- Comentat: Random Forest Evaluation ---
# y_pred_rf = rating_predictor.rf.predict(rating_predictor.scaler.transform(X))
# y_pred_rf = np.clip(np.round(y_pred_rf), 1, 10).astype(int)
# report_rf = classification_report(y, y_pred_rf, digits=4)
# cm_rf = confusion_matrix(y, y_pred_rf, labels=range(1, 11))
# acc_rf = accuracy_score(y, y_pred_rf)
# plt.figure(figsize=(6, 5))
# plt.imshow(cm_rf, cmap='Greens')
# plt.title(f'Random Forest Confusion Matrix\nAccuracy: {acc_rf:.4f}')
# plt.xlabel('Predicted')
# plt.ylabel('Actual')
# plt.colorbar()
# plt.tight_layout()
# plt.savefig("eval/rf_confusion_matrix.svg")
# plt.close()
# with open("eval/rf_classification_report.txt", "w") as f:
#     f.write(report_rf)
