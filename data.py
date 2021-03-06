import pickle
from os import path
import pandas as pd
import numpy as np
from sigsev_guard import sigsev_guard

ENABLE_UMAP = False
model_path = 'model/iii/'
parsed_docs_file = model_path + 'spacy-docs/iii-spacy-docs'
total = 291415

if ENABLE_UMAP:
    import umap

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


# @sigsev_guard(default_value=None, timeout=500)
def load_and_reduce_dim(name, dim, n_neighbors):
    embeddings = load_file(emb_filename(name))
    metric = 'cosine' if 'tfidf' not in name else 'hellinger'

    embeddings_mapped = umap.UMAP(n_neighbors=n_neighbors,
                                  n_components=dim,
                                  min_dist=0.0,
                                  low_memory=True,
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
    df.rename(columns={"date": "data", "kad": "kadencja", "okreg": "okr??g",
                       "posel": "pose??", "speaker": "m??wca", "text": "tre????"}, inplace=True)

    doc_words = load_file('tfidf-morf-top-words.pkl')
    df['opis'] = [' | '.join(w) for w in doc_words]

    df['okr??g'] = df['okr??g'].replace('Gorz??w', 'Gorz??w Wielkopolski')

    wojew = pickle.load(open('/home/marcin/mgr/parsed/wojew.pkl', 'rb'))
    df['wojew??dztwo'] = [wojew[o] if o != 'b/d' else 'b/d' for o in df['okr??g']]

    topics = load_file('topics.pkl')
    df['temat'] = topics

    embeddings_3d = load_embeddings(LEXRANK_WEIGHTED, dim=3)
    df['embedding_3d'] = np.asarray(embeddings_3d).tolist()

    embeddings_2d = load_embeddings(LEXRANK_WEIGHTED, dim=2)
    df['embedding_2d'] = np.asarray(embeddings_2d).tolist()

    return df


def drop_text(df):
    return df.drop(columns="tre????")


def load(kad):
    with open(f'{parsed_docs_file}-{kad}.pkl', "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def load_doc_tokens():
    return (tokens for kad in range(1,9) for tokens in load(kad))