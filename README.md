# Sistema de Recomendação de Filmes com Grafos (MovieLens + Neo4j)

Filtragem colaborativa item-item sobre o MovieLens 20M: correlação de Pearson entre filmes, regressão KNN para prever notas e armazenamento dos dados e das similaridades em um grafo Neo4j.

## Nomes

Lucas Pinheiro da Costa  \
Matheus Dutra  \
Pedro H. Lira

## Estrutura do repositório

```
config.py             parâmetros (conexão, amostra, similaridade, KNN, avaliação)
recsys.py             regressão KNN e recomendação, em Cypher
01_load_data.py       lê rating.csv e movie.csv, amostra e separa treino/teste
02_insert_graph.py    insere User, Movie, Genre, RATED e HAS_GENRE
03_similarity.py      calcula Pearson item-item e insere SIMILAR_TO
04_queries.py         consultas e agregações
05_evaluate.py        Precision@N e Recall@N
requirements.txt      neo4j, pandas, numpy
```

## Modelagem do grafo

| Elemento | Tipo | Atributos |
|---|---|---|
| `(:User)` | nó | `userId` |
| `(:Movie)` | nó | `movieId`, `title`, `year` (extraído do título) |
| `(:Genre)` | nó | `name` |
| `(:User)-[:RATED]->(:Movie)` | aresta | `rating` |
| `(:Movie)-[:HAS_GENRE]->(:Genre)` | aresta | — |
| `(:Movie)-[:SIMILAR_TO]->(:Movie)` | aresta | `corr` (Pearson), `common` (número de usuários que avaliaram os dois filmes) |

Só as avaliações do conjunto de treino entram no grafo. O conjunto de teste fica fora do banco e é usado apenas em `05_evaluate.py`.

## Método

**Dados.** `rating.csv` e `movie.csv` do MovieLens 20M (Kaggle). Amostra: os `N_MOVIES` filmes mais avaliados e `N_USERS` usuários sorteados (semente `SEED`) entre os que têm pelo menos `MIN_USER_RATINGS` avaliações nesses filmes.

**Separação treino/teste.** Para cada usuário, as avaliações são embaralhadas e 80% vão para treino e 20% para teste.

**Correlação de Pearson entre os filmes i e j** (`03_similarity.py`), calculada só sobre o treino:

```
c(i,j) = Σk (r_ik − r̄_i)(r_jk − r̄_j) / ( √Σk (r_ik − r̄_i)²  ·  √Σk (r_jk − r̄_j)² )
```

onde k percorre os usuários que avaliaram i e j, `r_ik` é a nota do usuário k ao filme i e `r̄_i` é a nota média do filme i no treino. Só são aceitos pares com pelo menos `MIN_COMMON` usuários em comum. Para cada filme, são gravados como arestas `SIMILAR_TO` os `TOP_NEIGHBORS` vizinhos de maior |c|.

**Regressão KNN** (`recsys.py`). Nota prevista para o usuário u no filme i:

```
r̂(u,i) = Σ c(i,j) · r(u,j)  /  Σ |c(i,j)|
```

com j percorrendo os `K` vizinhos de i de maior |c| (entre as arestas `SIMILAR_TO` de i) que o usuário u avaliou. Só são recomendados filmes que u ainda não avaliou no treino e que tenham pelo menos `MIN_NEIGHBORS` vizinhos avaliados por u. A recomendação devolve os `TOP_N` filmes de maior nota prevista.

**Avaliação** (`05_evaluate.py`). Filme relevante: nota ≥ `RELEVANT` no conjunto de teste. São sorteados `EVAL_USERS` usuários entre os que têm pelo menos um filme relevante no teste. Para cada um, calcula-se:

- Precision@N = (recomendados que são relevantes) / (recomendados);
- Recall@N = (recomendados que são relevantes) / (relevantes do usuário).

Os valores reportados são as médias entre os usuários que receberam recomendação.

## Parâmetros da configuração final (`config.py`)

| Parâmetro | Valor |
|---|---|
| `SEED` | 42 |
| `N_MOVIES` / `N_USERS` | 2000 / 8000 |
| `MIN_USER_RATINGS` | 20 |
| `TEST_FRACTION` | 0,2 |
| `MIN_COMMON` | 10 |
| `TOP_NEIGHBORS` | 200 |
| `K` | 20 |
| `MIN_NEIGHBORS` | 3 |
| `TOP_N` | 10 |
| `RELEVANT` | 4,0 |
| `EVAL_USERS` | 300 |

## Como executar

1. Suba um Neo4j 5 local, acessível apenas pela própria máquina:

```bash
export NEO4J_PASSWORD='sua-senha-forte'

docker run -d --name neo4j-movielens \
  -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
  -e NEO4J_AUTH="neo4j/$NEO4J_PASSWORD" \
  -v neo4j_data:/data \
  neo4j:5
```

Aguarde `Started.` em `docker logs neo4j-movielens`. Os scripts leem `NEO4J_URI`, `NEO4J_USER` e `NEO4J_PASSWORD` do ambiente.

2. Instale as dependências:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Baixe o [MovieLens 20M no Kaggle](https://www.kaggle.com/datasets/grouplens/movielens-20m-dataset) e coloque `rating.csv` e `movie.csv` em `data/raw/`.

4. Execute, na ordem, no mesmo terminal em que `NEO4J_PASSWORD` foi definida:

```bash
python3 01_load_data.py
python3 02_insert_graph.py
python3 03_similarity.py
python3 04_queries.py [userId]
python3 05_evaluate.py
```

## Resultados

Todos os números abaixo vêm de execuções reais dos scripts, com a configuração final, exceto onde indicado.

### Dados e grafo

| Item | Valor |
|---|---|
| Dataset bruto | 20.000.263 avaliações, 27.278 filmes |
| Amostra | 8.000 usuários, 2.000 filmes |
| Treino | 770.257 avaliações |
| Teste | 196.527 avaliações |
| Nós `Movie` | 2.000 |
| Nós `User` | 8.000 |
| Arestas `RATED` | 770.257 |
| Arestas `SIMILAR_TO` | 400.000 |

### Consultas para o usuário 20

**1) Comédias avaliadas com nota ≥ 4:** 2.

| Filme | Nota |
|---|---|
| Fear and Loathing in Las Vegas (1998) | 5,0 |
| Monty Python's Life of Brian (1979) | 4,0 |

**2) Gêneros mais avaliados pelo usuário 20:**

| Gênero | Avaliações | Média |
|---|---|---|
| Comedy | 9 | 3,11 |
| Drama | 8 | 4,13 |
| Adventure | 7 | 3,57 |
| Thriller | 7 | 3,64 |
| Action | 6 | 3,33 |

**6) Top 10 recomendações para o usuário 20** (KNN, k = 20):

| # | movieId | Filme | Nota prevista | Vizinhos usados |
|---|---|---|---|---|
| 1 | 53123 | Once (2006) | 4,45 | 3 |
| 2 | 2959 | Fight Club (1999) | 4,38 | 3 |
| 3 | 288 | Natural Born Killers (1994) | 4,37 | 3 |
| 4 | 46 | How to Make an American Quilt (1995) | 4,37 | 3 |
| 5 | 32 | Twelve Monkeys (a.k.a. 12 Monkeys) (1995) | 4,37 | 3 |
| 6 | 3535 | American Psycho (2000) | 4,34 | 3 |
| 7 | 1252 | Chinatown (1974) | 4,34 | 3 |
| 8 | 750 | Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1964) | 4,33 | 3 |
| 9 | 1258 | Shining, The (1980) | 4,31 | 6 |
| 10 | 879 | Relic, The (1997) | 4,28 | 3 |

### Agregações sobre todo o grafo

**3) Filmes mais bem avaliados** (mínimo de 100 avaliações):

| Filme | Avaliações | Média |
|---|---|---|
| Shawshank Redemption, The (1994) | 2.981 | 4,44 |
| Godfather, The (1972) | 1.944 | 4,39 |
| Usual Suspects, The (1995) | 2.222 | 4,34 |
| Schindler's List (1993) | 2.329 | 4,31 |
| Godfather: Part II, The (1974) | 1.301 | 4,29 |
| Sunset Blvd. (a.k.a. Sunset Boulevard) (1950) | 305 | 4,27 |
| One Flew Over the Cuckoo's Nest (1975) | 1.402 | 4,27 |
| Thin Man, The (1934) | 150 | 4,27 |
| Band of Brothers (2001) | 199 | 4,27 |
| Rear Window (1954) | 840 | 4,26 |

**4) Média de nota por gênero:**

| Gênero | Avaliações | Média |
|---|---|---|
| Film-Noir | 8.498 | 4,00 |
| War | 41.890 | 3,87 |
| Documentary | 3.995 | 3,85 |
| Drama | 334.249 | 3,74 |
| Crime | 135.249 | 3,74 |
| IMAX | 19.624 | 3,72 |
| Mystery | 63.963 | 3,71 |
| Animation | 46.526 | 3,66 |
| Western | 16.313 | 3,60 |
| Romance | 150.451 | 3,59 |
| Musical | 34.704 | 3,59 |
| Fantasy | 88.160 | 3,56 |
| Thriller | 216.954 | 3,56 |
| Adventure | 188.118 | 3,55 |
| Comedy | 290.683 | 3,50 |
| Action | 237.622 | 3,50 |
| Children | 67.700 | 3,49 |
| Sci-Fi | 134.036 | 3,47 |
| Horror | 51.554 | 3,42 |

**5) Filmes mais similares a Toy Story (1995)** (correlação de Pearson):

| Filme | Correlação | Usuários em comum |
|---|---|---|
| Toy Story 2 (1999) | 0,689 | 696 |
| Bug's Life, A (1998) | 0,553 | 582 |
| Incredibles, The (2004) | 0,532 | 538 |
| Monsters, Inc. (2001) | 0,515 | 662 |
| Finding Nemo (2003) | 0,508 | 651 |
| General, The (1926) | 0,505 | 61 |
| Celebration, The (Festen) (1998) | 0,502 | 41 |
| Toy Story 3 (2010) | 0,498 | 151 |
| Doctor Dolittle (1967) | 0,475 | 42 |
| 101 Dalmatians (One Hundred and One Dalmatians) (1961) | 0,454 | 208 |

### Avaliação do modelo (top-10, K = 20)

Configuração final e uma execução anterior com `TOP_NEIGHBORS = 50` (demais parâmetros iguais):

| `TOP_NEIGHBORS` | Arestas `SIMILAR_TO` | Usuários avaliados | Sem recomendação | Precision@10 | Recall@10 | F1@10 |
|---|---|---|---|---|---|---|
| 50 | 100.000 | 290 | 10 | 0,0423 | 0,0303 | 0,0353 |
| 200 (final) | 400.000 | 300 | 0 | 0,0383 | 0,0259 | 0,0309 |

F1@10 = 2·P·R / (P + R), calculado sobre as médias.

### Execução com amostra maior

Execução com 5000 filmes e 20000 usuários (`TOP_NEIGHBORS = 200`, `K = 20`, top-10):

| Item | Valor |
|---|---|
| Treino / teste | 2.217.755 / 564.253 avaliações |
| Arestas `SIMILAR_TO` | 1.000.000 |
| Usuários avaliados / sem recomendação | 300 / 0 |
| Precision@10 | 0,0170 |
| Recall@10 | 0,0087 |
| F1@10 | 0,0115 |
