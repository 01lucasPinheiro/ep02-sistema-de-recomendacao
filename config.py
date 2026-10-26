import os

# --- Neo4j ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j12345")

# --- Amostragem do dataset (20M é grande demais para um Neo4j local) ---
SEED = 42
N_MOVIES = 2000          # filmes mais avaliados
N_USERS = 8000           # usuários sorteados
MIN_USER_RATINGS = 20    # usuários com poucas avaliações são descartados
TEST_FRACTION = 0.2      # 80% treino / 20% teste (por usuário)

# --- Similaridade (Pearson item-item) ---
MIN_COMMON = 10          # mínimo de usuários em comum para aceitar a correlação
TOP_NEIGHBORS = 200       # vizinhos guardados por filme (arestas SIMILAR_TO)

# --- KNN / recomendação ---
K = 20                   # vizinhos usados na regressão
MIN_NEIGHBORS = 3        # mínimo de vizinhos avaliados pelo usuário para prever
TOP_N = 10               # tamanho da lista de recomendação

# --- Avaliação ---
RELEVANT = 4.0           # nota >= 4 no teste = filme relevante
EVAL_USERS = 300         # usuários de teste avaliados

DATA_DIR = "data"
