import pickle
from os import path
import pandas as pd
import numpy as np
from sigsev_guard import sigsev_guard

ENABLE_UMAP = False
model_path = '/data/model/iii/'
parsed_docs_file = model_path + 'spacy-docs/iii-spacy-docs'
total = 291415

if ENABLE_UMAP:
    import umap

DEFAULT, MEAN, LEXRANK_TOP1, LEXRANK_TOP5, LEXRANK_WEIGHTED, TFIDF_TOP1, TFIDF_TOP5, TFIDF_WEIGHTED, TFIDF_MORF = 'default', 'mean', 'lexrank-top1', 'lexrank-top5', 'lexrank-weighted', 'tfidf-top1', 'tfidf-top5', 'tfidf-weighted', 'tfidf-morf'
LEXRANK_TOP1xTFIDF, LEXRANK_TOP3xTFIDF, LEXRANK_WEIGHTEDxTFIDF = 'lexrank-top1-xtfidf', 'lexrank-top3-xtfidf', 'lexrank-weighted-xtfidf'


def emb_filename(emb, dim=None, n_neighbors=None):
    filename = emb if '.pkl' not in emb else emb[:-4]
    if dim is not None:
        filename = f'mapped/{filename}-{dim}d-{n_neighbors}'

    return 'embeddings/' + filename + '.pkl'


def save_file(obj, name):
    pickle.dump(obj, open(model_path + name, 'wb'))


def load_file(name):
    return pickle.load(open(model_path + name, 'rb'))


def file_exists(name):
    return path.exists(model_path + name)


@sigsev_guard(default_value=None, timeout=500)
def load_and_reduce_dim(name, dim, n_neighbors):
    embeddings = load_file(emb_filename(name))
    metric = 'cosine' if 'tfidf' not in name else 'hellinger'

    embeddings_mapped = umap.UMAP(n_neighbors=n_neighbors,
                                  n_components=dim,
                                  min_dist=0.0,
                                  metric=metric).fit_transform(embeddings)

    save_file(embeddings_mapped, emb_filename(name, dim, n_neighbors))
    return embeddings_mapped


def load_embeddings(name, dim=5, n_neighbors=15):
    filename_ = emb_filename(name, dim, n_neighbors)

    if file_exists(filename_):
        return load_file(filename_)

    if not ENABLE_UMAP:
        raise Exception('File not found and UMAP not enabled')

    print(f'{filename_} not found, generating from full embeddings')
    embeddings_mapped = load_and_reduce_dim(name, dim, n_neighbors)

    return embeddings_mapped

def load_stopwords():
    with open('polish_stopwords.txt') as f:
        stop_words = [x.strip() for x in f]
    return set(stop_words)

def load_clean_df():
    df = pd.read_csv(model_path + 'iii.csv', index_col=0)
    df.fillna('b/d', inplace=True)
    df.rename(columns={"date": "data", "kad": "kadencja", "okreg": "okręg",
                       "posel": "poseł", "speaker": "mówca", "text": "treść"}, inplace=True)

    doc_words = load_file('tfidf-morf-top-words.pkl')
    df['opis'] = [' | '.join(w) for w in doc_words]

    df['okręg'] = df['okręg'].replace('Gorzów', 'Gorzów Wielkopolski')

    wojew = pickle.load(open('/home/marcin/mgr/parsed/wojew.pkl', 'rb'))
    df['województwo'] = [wojew[o] if o != 'b/d' else 'b/d' for o in df['okręg']]

    topics = load_file('topics.pkl')
    df['temat'] = topics

    embeddings_3d = load_embeddings(LEXRANK_WEIGHTED, dim=3)
    df['embedding_3d'] = np.asarray(embeddings_3d).tolist()

    embeddings_2d = load_embeddings(LEXRANK_WEIGHTED, dim=2)
    df['embedding_2d'] = np.asarray(embeddings_2d).tolist()

    return df


def drop_text(df):
    return df.drop(columns="treść")


def load(kad):
    with open(f'{parsed_docs_file}-{kad}.pkl', "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def load_doc_tokens():
    return (tokens for kad in range(1,9) for tokens in load(kad))