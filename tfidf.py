from sklearn.feature_extraction.text import TfidfVectorizer
from tfidf_morfeusz import MorfeuszAnalyser
import pandas as pd
import numpy as np
import pickle
from multiprocessing import Pool
from tqdm import tqdm

model_path = 'model/iii/'
doc_file = model_path + 'iii.csv'

total = 291415

df_reader = pd.read_csv(doc_file, usecols=['text'], chunksize=10000)
docs_gen = (x for df in df_reader for x in df.text.to_list())

analyser = MorfeuszAnalyser()

print("generating lemmatized ngrams..")
with Pool(8) as p:
    docs = list(tqdm(p.imap(analyser, docs_gen), total=total))

print("calculating tf-idf..")
tfidf_vectorizer = TfidfVectorizer(analyzer=lambda x: x, min_df=5)
embeddings_tfidf = tfidf_vectorizer.fit_transform(tqdm(docs, total=total))

print("Saving embeddings..")

with open(model_path + 'tfidf-morf.pkl', "wb") as fOut:
    pickle.dump(embeddings_tfidf, fOut)

print("done")

feature_names = np.array(tfidf_vectorizer.get_feature_names())

def get_top_tf_idf_words(response, top_n=5):
    sorted_emb = np.argsort(response.data)[:-(top_n+1):-1]
    return feature_names[response.indices[sorted_emb]]

tfidf_words = [get_top_tf_idf_words(x) for x in embeddings_tfidf]

print("Saving words..")
with open(model_path + 'tfidf-morf-top-words.pkl', "wb") as fOut:
    pickle.dump(tfidf_words, fOut)
