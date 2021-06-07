from data import model_path, load_embeddings
from tqdm import tqdm
from glob import glob

skip = [
    ('sbert-lexrank-top1', 5),
    ('sbert-lexrank-top1', 10),
    ('sbert-tf-idf-top1', 5),
    ('sbert-tf-idf-top1', 10),
    ('use-lexrank-top1', 5),
    ('use-lexrank-top1', 10),
    ('use-tf-idf-top1', 5),
    ('use-tf-idf-top1', 10),
    ('use-tf-idf-top1', 15),
    ('use-tf-idf-top1', 20),
    ('use-tf-idf-top5', 5),
    ('use-tf-idf-top5', 10),
]

for emb_file in tqdm(sorted(glob(model_path + 'embeddings/*.pkl')), position=0):
    emb = emb_file.split('/')[-1][:-4]

    for n_neighbors in tqdm([5, 10, 15, 20, 25, 50], position=1, leave=False):
        if (emb, n_neighbors) in skip:
            continue
        if 'top' in emb and n_neighbors in [25, 50]:
            continue
        load_embeddings(emb, dim=5, n_neighbors=n_neighbors)