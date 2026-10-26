import numpy as np
import pandas as pd
from neo4j import GraphDatabase
import config as cfg
import recsys


def main():
    test = pd.read_csv(f"{cfg.DATA_DIR}/test.csv")
    relevant = test[test["rating"] >= cfg.RELEVANT].groupby("userId")["movieId"].apply(set)

    rng = np.random.default_rng(cfg.SEED)
    users = rng.choice(relevant.index.to_numpy(), size=min(cfg.EVAL_USERS, len(relevant)), replace=False)

    precisions, recalls, no_recs = [], [], 0
    driver = GraphDatabase.driver(cfg.NEO4J_URI, auth=(cfg.NEO4J_USER, cfg.NEO4J_PASSWORD))
    with driver.session() as s:
        for uid in users:
            recs = recsys.recommend(s, int(uid), cfg.K, cfg.MIN_NEIGHBORS, cfg.TOP_N)
            if not recs:
                no_recs += 1
                continue
            rec_ids = {r["movieId"] for r in recs}
            hits = len(rec_ids & relevant[uid])
            precisions.append(hits / len(rec_ids))
            recalls.append(hits / len(relevant[uid]))
    driver.close()

    p, r = float(np.mean(precisions)), float(np.mean(recalls))
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    print(f"Usuarios avaliados: {len(precisions)} (sem recomendacao: {no_recs})")
    print(f"Precision@{cfg.TOP_N}: {p:.4f}")
    print(f"Recall@{cfg.TOP_N}:    {r:.4f}")
    print(f"F1@{cfg.TOP_N}:        {f1:.4f}")


if __name__ == "__main__":
    main()
