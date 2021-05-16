from sklearn.feature_extraction.text import TfidfVectorizer
from morfeusz_spacy_analyser import SpacyMorfeuszAnalyser
import pandas as pd
import numpy as np
import pickle
from multiprocessing import Pool
from tqdm import tqdm

model_path = '/data/model/iii/'
parsed_docs_file = model_path + 'spacy-docs/iii-spacy-docs'
total = 291415

def load(kad):
    with open(f'{parsed_docs_file}-{kad}.pkl', "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

tokens = (tokens for kad in range(1,9) for tokens in load(kad))

tfidf_vectorizer = TfidfVectorizer(analyzer=lambda x: x, min_df=5)
embeddings_tfidf = tfidf_vectorizer.fit_transform(tqdm(tokens, total=total))

print("Saving embeddings..")

with open(model_path + 'tfidf-morf.pkl', "wb") as fOut:
    pickle.dump(embeddings_tfidf, fOut)

print("done")

feature_names = np.array(tfidf_vectorizer.get_feature_names())

def get_top_tf_idf_words(response, top_n=10):
    sorted_emb = np.argsort(response.data)[:-(top_n+1):-1]
    return feature_names[response.indices[sorted_emb]]

tfidf_words = [get_top_tf_idf_words(x) for x in embeddings_tfidf]

print("Saving words..")
with open(model_path + 'tfidf-morf-top-words.pkl', "wb") as fOut:
    pickle.dump(tfidf_words, fOut)
