FROM tensorflow/tensorflow:2.3.2-gpu-jupyter

RUN apt update && \
    apt install -y wget

RUN pip install --upgrade pip

RUN wget -O - http://download.sgjp.pl/apt/sgjp.gpg.key|apt-key add -
RUN apt-add-repository http://download.sgjp.pl/apt/ubuntu
RUN apt update && \
    apt install -y morfeusz2 python3-morfeusz2

RUN pip install spacy==2.2.4 cupy-cuda101

RUN wget -q -O pl_morf.tar.gz "http://zil.ipipan.waw.pl/SpacyPL?action=AttachFile&do=get&target=pl_spacy_model_morfeusz-0.1.3.tar.gz" && \
    python -m pip install ./pl_morf.tar.gz && \
    rm ./pl_morf.tar.gz

RUN pip install nltk pandas scikit-learn tqdm

RUN python -c "import nltk; nltk.download('punkt')"

# fix (if using CUDA) - remove if using CPU
# TypeError: Implicit conversion to a NumPy array is not allowed. Please use `.get()` to construct a NumPy array explicitly.
RUN sed -i 's/tok.vector/tok.vector.get()/' \
    /usr/local/lib/python3.6/dist-packages/pl_spacy_model_morfeusz/preprocessor/Toygger/__init__.py

# fix obscure KeyError
RUN sed -i 's/position_to_analyses[ind] == []/position_to_analyses.get(ind, []) == []' \
    /usr/local/lib/python3.6/dist-packages/pl_spacy_model_morfeusz/preprocessor/__init__.py