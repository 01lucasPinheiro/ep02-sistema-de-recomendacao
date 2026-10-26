"""Correlação de Pearson item-item (treino) e gravação das arestas SIMILAR_TO no grafo.

c(i,j) = sum_k (r_ik - mean_i)(r_jk - mean_j)
         / ( sqrt(sum_k (r_ik - mean_i)^2) * sqrt(sum_k (r_jk - mean_j)^2) )
com k percorrendo apenas os usuários que avaliaram i e j.
"""
import numpy as np
import pandas as pd
from neo4j import GraphDatabase
import config as cfg


def pearson_matrix(train, movie_ids):
    mid_idx = {m: i for i, m in enumerate(movie_ids)}
    uid_idx = {u: i for i, u in enumerate(train["userId"].unique())}
    u = train["userId"].map(uid_idx).to_numpy()
    m = train["movieId"].map(mid_idx).to_numpy()

    R = np.zeros((len(uid_idx), len(movie_ids)), dtype=np.float32)
    R[u, m] = train["rating"].to_numpy(dtype=np.float32)
    M = (R > 0).astype(np.float32)                       

    cnt = M.sum(axis=0)
    mean = np.divide(R.sum(axis=0), cnt, out=np.zeros_like(cnt), where=cnt > 0)
    C = (R - mean) * M                                   
    num = C.T @ C                                        
    d1 = (C ** 2).T @ M                                  
    den = np.sqrt(d1 * d1.T)
    corr = np.divide(num, den, out=np.zeros_like(num), where=den > 1e-9)
    common = M.T @ M
    return corr, common


def main():
    train = pd.read_csv(f"{cfg.DATA_DIR}/train.csv")
    movie_ids = pd.read_csv(f"{cfg.DATA_DIR}/movies.csv")["movieId"].tolist()
    corr, common = pearson_matrix(train, movie_ids)

    valid = common >= cfg.MIN_COMMON
    np.fill_diagonal(valid, False)
    score = np.where(valid, corr, -1.0)
    k = min(cfg.TOP_NEIGHBORS, len(movie_ids) - 1)
    top = np.argpartition(-score, k, axis=1)[:, :k]      # k vizinhos de maior |c| por filme

    rows = []
    for i in range(len(movie_ids)):
        for j in top[i]:
            if valid[i, j]:
                rows.append({"a": int(movie_ids[i]), "b": int(movie_ids[j]),
                             "corr": float(corr[i, j]), "n": int(common[i, j])})
    print(f"{len(rows)} arestas SIMILAR_TO")

    driver = GraphDatabase.driver(cfg.NEO4J_URI, auth=(cfg.NEO4J_USER, cfg.NEO4J_PASSWORD))
    with driver.session() as s:
        s.run("MATCH ()-[r:SIMILAR_TO]->() CALL { WITH r DELETE r } IN TRANSACTIONS OF 10000 ROWS")
        for i in range(0, len(rows), 5000):
            s.run("""
                UNWIND $rows AS row
                MATCH (a:Movie {movieId: row.a}), (b:Movie {movieId: row.b})
                CREATE (a)-[:SIMILAR_TO {corr: row.corr, common: row.n}]->(b)
            """, rows=rows[i:i + 5000])
    driver.close()


if __name__ == "__main__":
    main()
