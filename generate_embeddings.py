from data import model_path, load_embeddings
from tqdm import tqdm
from glob import glob

for emb_file in tqdm(sorted(glob(model_path + 'embeddings/*.pkl')), position=0):
    emb = emb_file.split('/')[-1][:-4]

    for n_neighbors in tqdm([5, 10, 15, 20], position=1, leave=False):
        load_embeddings(emb, dim=5, n_neighbors=n_neighbors)