from glob import glob
from tqdm import tqdm
import pickle

emb_path='model/iii/'

emb_types = ['lexrank-top1.pkl','lexrank-top3.pkl','lexrank-weighted.pkl','tfidf-top1.pkl','tfidf-top3.pkl','tfidf-weighted.pkl']

def load_embeddings(name):
    all_embeddings = []
    for kad in sorted(glob(emb_path + '*/')):
        embeddings = pickle.load(open(kad + name, "rb"))
        all_embeddings.extend(embeddings)
    
    return all_embeddings

for emb_type in tqdm(emb_types):
    emb = load_embeddings(emb_type)
    pickle.dump(emb, open(emb_path + emb_type, "wb"))
