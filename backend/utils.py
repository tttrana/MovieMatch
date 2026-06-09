import numpy as np

def extract_features(movie, mlb_genres, return_names=False):
    # Genres as binary vector double weight
    genres_list = movie.genres.split(", ") if movie.genres else []
    genres_vec = mlb_genres.transform([genres_list])[0]
    genres_vec = np.concatenate([genres_vec, genres_vec])  # double weight

    # Numeric features
    avg_rating = movie.averageRating if movie.averageRating is not None else 0.0
    num_votes = movie.numVotes if movie.numVotes is not None else 0

    # Combine all features
    features = np.concatenate([genres_vec, [avg_rating, num_votes]])

    if return_names:
        genre_names = list(mlb_genres.classes_) * 2  # double weight
        feature_names = genre_names + ["averageRating", "numVotes"]
        return features, feature_names
    return features