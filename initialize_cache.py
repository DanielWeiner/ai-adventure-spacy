import huggingface_hub
from transformers.utils.hub import move_cache
from amrlib.alignments.faa_aligner import FAA_Aligner

if __name__ == '__main__':
    huggingface_hub.snapshot_download('facebook/bart-large', allow_patterns=['*.txt', '*.json'])
    FAA_Aligner()
    move_cache()