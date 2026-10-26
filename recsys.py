"""Regressão KNN item-item feita em Cypher.

r_hat(u,i) = sum_{j in N_k(i)} c(i,j) * r(u,j)  /  sum_{j in N_k(i)} |c(i,j)|
onde N_k(i) = os k vizinhos de i (maior |c|) que o usuário u avaliou.
"""

PREDICT = """
MATCH (i:Movie {movieId: $mid})-[s:SIMILAR_TO]->(j:Movie)<-[r:RATED]-(u:User {userId: $uid})
WITH s, r ORDER BY abs(s.corr) DESC LIMIT $k
RETURN sum(s.corr * r.rating) AS num, sum(abs(s.corr)) AS den, count(*) AS n
"""

RECOMMEND = """
MATCH (u:User {userId: $uid})-[r:RATED]->(j:Movie)<-[s:SIMILAR_TO]-(i:Movie)
WHERE NOT (u)-[:RATED]->(i)
WITH i, s, r ORDER BY abs(s.corr) DESC
WITH i, collect({c: s.corr, r: r.rating})[0..$k] AS nb
WHERE size(nb) >= $min_nb
WITH i, nb,
     reduce(num = 0.0, x IN nb | num + x.c * x.r) AS num,
     reduce(den = 0.0, x IN nb | den + abs(x.c)) AS den
WHERE den > 0
RETURN i.movieId AS movieId, i.title AS title, num / den AS pred, size(nb) AS neighbors
ORDER BY pred DESC, neighbors DESC
LIMIT $n
"""


def predict_rating(session, uid, mid, k):
    rec = session.run(PREDICT, uid=uid, mid=mid, k=k).single()
    if rec is None or rec["n"] == 0 or rec["den"] == 0:
        return None
    return rec["num"] / rec["den"]


def recommend(session, uid, k, min_nb, n):
    return session.run(RECOMMEND, uid=uid, k=k, min_nb=min_nb, n=n).data()
