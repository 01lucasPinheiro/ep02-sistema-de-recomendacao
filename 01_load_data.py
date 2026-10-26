"""le rating.csv e movie.csv, amostra os dados e separa treino/teste (80/20 por usuario)."""
import os
import numpy as np
import pandas as pd
import config as cfg

RATINGS_PATH = os.path.join(cfg.DATA_DIR, "raw", "rating.csv")
MOVIES_PATH = os.path.join(cfg.DATA_DIR, "raw", "movie.csv")


def main():
    for path in (RATINGS_PATH, MOVIES_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"arquivo nao encontrado: {path} (coloque os csvs em data/raw/)")

    ratings = pd.read_csv(RATINGS_PATH, usecols=["userId", "movieId", "rating"])
    movies = pd.read_csv(MOVIES_PATH)
    print(f"bruto: {len(ratings):,} avaliacoes, {len(movies):,} filmes")

    # amostra: filmes mais avaliados e usuarios sorteados com avaliacoes suficientes
    top_movies = ratings["movieId"].value_counts().head(cfg.N_MOVIES).index
    r = ratings[ratings["movieId"].isin(top_movies)]

    counts = r["userId"].value_counts()
    eligible = counts[counts >= cfg.MIN_USER_RATINGS].index.to_numpy()
    rng = np.random.default_rng(cfg.SEED)
    users = rng.choice(eligible, size=min(cfg.N_USERS, len(eligible)), replace=False)
    r = r[r["userId"].isin(users)]

    # split 80/20 por usuario: embaralha e corta as avaliacoes de cada usuario
    r = r.sample(frac=1.0, random_state=cfg.SEED)
    pos = r.groupby("userId").cumcount()
    size = r.groupby("userId")["userId"].transform("size")
    is_test = pos >= np.floor(size * (1 - cfg.TEST_FRACTION))
    train, test = r[~is_test], r[is_test]

    # filmes da amostra, com o ano extraido do titulo
    movies = movies[movies["movieId"].isin(top_movies)].copy()
    movies["year"] = pd.to_numeric(movies["title"].str.extract(r"\((\d{4})\)\s*$")[0])

    os.makedirs(cfg.DATA_DIR, exist_ok=True)
    train.to_csv(f"{cfg.DATA_DIR}/train.csv", index=False)
    test.to_csv(f"{cfg.DATA_DIR}/test.csv", index=False)
    movies.to_csv(f"{cfg.DATA_DIR}/movies.csv", index=False)
    print(f"amostra: {r['userId'].nunique():,} usuarios, {len(movies):,} filmes")
    print(f"treino: {len(train):,} | teste: {len(test):,}")


if __name__ == "__main__":
    main()