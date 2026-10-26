"""consultas e agregacoes. uso: python 04_queries.py [userId]"""
import sys
from neo4j import GraphDatabase
import config as cfg
import recsys


def show(title, rows):
    print(f"\n=== {title} ===")
    for r in rows:
        print(r)


def main():
    driver = GraphDatabase.driver(cfg.NEO4J_URI, auth=(cfg.NEO4J_USER, cfg.NEO4J_PASSWORD))
    with driver.session() as s:
        uid = int(sys.argv[1]) if len(sys.argv) > 1 else \
            s.run("MATCH (u:User) RETURN u.userId AS id ORDER BY id LIMIT 1").single()["id"]
        print(f"usuario x = {uid}")

        show("1) comedias que o usuario x assistiu e avaliou com nota >= 4", s.run("""
            MATCH (u:User {userId: $uid})-[r:RATED]->(m:Movie)-[:HAS_GENRE]->(:Genre {name: 'Comedy'})
            WHERE r.rating >= 4
            RETURN count(m) AS total_comedias_nota_4_ou_mais
        """, uid=uid).data())

        show("   (lista das 10 melhores)", s.run("""
            MATCH (u:User {userId: $uid})-[r:RATED]->(m:Movie)-[:HAS_GENRE]->(:Genre {name: 'Comedy'})
            WHERE r.rating >= 4
            RETURN m.title AS filme, r.rating AS nota ORDER BY nota DESC, filme LIMIT 10
        """, uid=uid).data())

        show("2) generos favoritos do usuario x (media e quantidade)", s.run("""
            MATCH (u:User {userId: $uid})-[r:RATED]->(:Movie)-[:HAS_GENRE]->(g:Genre)
            RETURN g.name AS genero, count(*) AS qtd, round(avg(r.rating), 2) AS media
            ORDER BY qtd DESC LIMIT 5
        """, uid=uid).data())

        show("3) filmes mais avaliados (min. 100 avaliacoes) com maior media", s.run("""
            MATCH (:User)-[r:RATED]->(m:Movie)
            WITH m, count(r) AS qtd, avg(r.rating) AS media WHERE qtd >= 100
            RETURN m.title AS filme, qtd, round(media, 2) AS media ORDER BY media DESC LIMIT 10
        """).data())

        show("4) media de nota por genero (todos os usuarios)", s.run("""
            MATCH (:User)-[r:RATED]->(:Movie)-[:HAS_GENRE]->(g:Genre)
            RETURN g.name AS genero, count(r) AS qtd, round(avg(r.rating), 2) AS media
            ORDER BY media DESC
        """).data())

        show("5) filmes mais similares a 'toy story' (pearson)", s.run("""
            MATCH (m:Movie)-[s:SIMILAR_TO]->(n:Movie) WHERE m.title STARTS WITH 'Toy Story (1995)'
            RETURN n.title AS filme, round(s.corr, 3) AS correlacao, s.common AS usuarios_em_comum
            ORDER BY s.corr DESC LIMIT 10
        """).data())

        show(f"6) top {cfg.TOP_N} recomendacoes para o usuario {uid} (knn, k={cfg.K})",
             recsys.recommend(s, uid, cfg.K, cfg.MIN_NEIGHBORS, cfg.TOP_N))
    driver.close()


if __name__ == "__main__":
    main()