import pickle
from os import path
import pandas as pd
import numpy as np

ENABLE_UMAP = False
SAVE_MAPS = False
model_path = '/data/model/iii/'

if ENABLE_UMAP:
    import umap

LEXRANK_TOP1,LEXRANK_TOP3,LEXRANK_WEIGHTED,TFIDF_TOP1,TFIDF_TOP3,TFIDF_WEIGHTED, TFIDF_MORF = 'lexrank-top1','lexrank-top3','lexrank-weighted','tfidf-top1','tfidf-top3','tfidf-weighted', 'tfidf-morf'
LEXRANK_TOP1xTFIDF, LEXRANK_TOP3xTFIDF, LEXRANK_WEIGHTEDxTFIDF = 'lexrank-top1-xtfidf','lexrank-top3-xtfidf','lexrank-weighted-xtfidf'

def filename(emb_type, dim=None, map=False):
    filename = emb_type 
    if dim is not None:
        filename += f'-{dim}d'
    if map:
        filename += '-map'

    return filename + '.pkl'

def save_file(obj, name):
    pickle.dump(obj, open(model_path + name, 'wb'))

def load_file(name):
    return pickle.load(open(model_path + name, 'rb'))

def file_exists(name):
    return path.exists(model_path + name)

def map_embeddings(embeddings, dim=5, metric='cosine'):
    return umap.UMAP(n_neighbors=15,
                     n_components=dim,
                     min_dist=0.0,
                     metric=metric).fit(embeddings)

def load_and_reduce_dim(name, dim):
    embeddings = load_file(filename(name))
    embeddings_map = map_embeddings(embeddings, dim)
    if SAVE_MAPS:
        save_file(embeddings_map, filename(name, dim, map=True))
    save_file(embeddings_map.embedding_, filename(name, dim))
    return embeddings_map

def load_embeddings(name, dim=5, map=False):
    filename_ = filename(name, dim, map)

    if file_exists(filename_):
        return load_file(filename_)

    if not ENABLE_UMAP:
        raise Exception('File not found and UMAP not enabled')

    if map:
        print(f'map {filename_} not found, generating from full embeddings')
        embeddings_map = load_and_reduce_dim(name, dim)
        return embeddings_map
    else:
        if file_exists(filename(name, dim, map=True)):
            print(f'embeddings {filename_} not found but found map for same dim')
            embeddings_map = load_file(filename(name, dim, map=True))
            save_file(embeddings_map.embedding_, filename(name, dim))
        else:
            print(f'embeddings {filename_} not found, generating from full embeddings')
            embeddings_map = load_and_reduce_dim(name, dim)

        return embeddings_map.embedding_

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