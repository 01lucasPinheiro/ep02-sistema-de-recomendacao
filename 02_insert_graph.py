"""Cria o grafo no Neo4j: User, Movie, Genre, RATED (só treino) e HAS_GENRE."""
import pandas as pd
from neo4j import GraphDatabase
import config as cfg


def batches(rows, size=5000):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def main():
    movies = pd.read_csv(f"{cfg.DATA_DIR}/movies.csv")
    train = pd.read_csv(f"{cfg.DATA_DIR}/train.csv")

    driver = GraphDatabase.driver(cfg.NEO4J_URI, auth=(cfg.NEO4J_USER, cfg.NEO4J_PASSWORD))
    with driver.session() as s:
        s.run("MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS")
        s.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE")
        s.run("CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movieId IS UNIQUE")
        s.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE")

        # Filmes + gêneros
        movie_rows = [
            {"movieId": int(r.movieId), "title": r.title,
             "year": int(r.year) if pd.notna(r.year) else None,
             "genres": str(r.genres).split("|")}
            for r in movies.itertuples()
        ]
        for b in batches(movie_rows):
            s.run("""
                UNWIND $rows AS row
                MERGE (m:Movie {movieId: row.movieId})
                SET m.title = row.title, m.year = row.year
                WITH m, row UNWIND row.genres AS g
                MERGE (ge:Genre {name: g})
                MERGE (m)-[:HAS_GENRE]->(ge)
            """, rows=b)
        print(f"{len(movie_rows)} filmes inseridos")

        # Usuários
        uids = train["userId"].unique().tolist()
        for b in batches(uids):
            s.run("UNWIND $ids AS id MERGE (:User {userId: id})", ids=b)
        print(f"{len(uids)} usuários inseridos")

        # Avaliações (apenas treino -> sem vazamento de dados)
        rating_rows = [{"userId": u, "movieId": m, "rating": float(r)}
                       for u, m, r in zip(train["userId"].tolist(),
                                          train["movieId"].tolist(),
                                          train["rating"].tolist())]
        for i, b in enumerate(batches(rating_rows)):
            s.run("""
                UNWIND $rows AS row
                MATCH (u:User {userId: row.userId})
                MATCH (m:Movie {movieId: row.movieId})
                CREATE (u)-[:RATED {rating: row.rating}]->(m)
            """, rows=b)
        print(f"{len(rating_rows)} arestas RATED inseridas")
    driver.close()


if __name__ == "__main__":
    main()
