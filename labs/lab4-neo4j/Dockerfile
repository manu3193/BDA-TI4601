# JupyterLab, el kernel y PyTorch CPU ya están en la imagen oficial.
# Torch se instaló ahí desde la rueda de download.pytorch.org; aquí no se compila nada.
FROM quay.io/jupyter/pytorch-notebook:python-3.13

USER root
COPY requirements.txt /tmp/requirements.txt
# No se reinstala torch: la imagen base ya trae la rueda CPU.
RUN python -c 'import torch; open("/tmp/torch-constraint.txt","w").write("torch==%s\n"%torch.__version__)' \
    && pip install --no-cache-dir -c /tmp/torch-constraint.txt -r /tmp/requirements.txt \
    && mkdir -p /models/hf \
    && chown -R ${NB_UID}:${NB_GID} /models

ENV HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf \
    MODELO_ID=Qwen/Qwen2.5-0.5B-Instruct \
    EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
    NEO4J_URI=bolt://neo4j:7687 \
    NEO4J_USERNAME=neo4j \
    NEO4J_PASSWORD=ti4601-grafos \
    JUPYTER_TOKEN=ti4601

USER ${NB_UID}
# Los dos modelos preentrenados quedan en la imagen para la sesión.
RUN python -c "from llama_index.embeddings.huggingface import HuggingFaceEmbedding; HuggingFaceEmbedding(model_name='${EMBED_MODEL}')" \
    && python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; import os; m=os.environ['MODELO_ID']; AutoTokenizer.from_pretrained(m); AutoModelForCausalLM.from_pretrained(m)"

WORKDIR /src
