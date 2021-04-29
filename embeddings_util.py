import pandas as pd
import numpy as np
import umap
import pickle
from os import path

LEXRANK_TOP1,LEXRANK_TOP3,LEXRANK_WEIGHTED,TFIDF_TOP1,TFIDF_TOP3,TFIDF_WEIGHTED, TFIDF_MORF = 'lexrank-top1','lexrank-top3','lexrank-weighted','tfidf-top1','tfidf-top3','tfidf-weighted', 'tfidf-morf'
LEXRANK_TOP1xTFIDF, LEXRANK_TOP3xTFIDF, LEXRANK_WEIGHTEDxTFIDF = 'lexrank-top1-xtfidf','lexrank-top3-xtfidf','lexrank-weighted-xtfidf'
model_path = 'model/iii/'

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
    save_file(embeddings_map, filename(name, dim, map=True))
    save_file(embeddings_map.embedding_, filename(name, dim))
    return embeddings_map

def load_embeddings(name, dim=5, map=False):
    filename_ = filename(name, dim, map)

    if file_exists(filename_):
        return load_file(filename_)

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