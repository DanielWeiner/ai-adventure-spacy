from typing import Callable
from src.fixed_dict import FixedDict
from spacy import Language

parse_result_defaults = {
    "tokens":         [],
    "noun_chunks":    [],
    "entities":       [],
    "coref_clusters": []
}

class ParseResults(FixedDict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(parse_result_defaults.keys(), *args, **kwargs)

def parse(get_nlp: Callable[[], Language], value: str):
    parse_results = ParseResults(parse_result_defaults)
    
    if not isinstance(value, str) or len(value) == 0:
        return parse_results
    
    nlp = get_nlp()
    doc = nlp(value)
    
    tokens = [{
        "index":            token.i,
        "char_index":       token.idx,
        "text":             token.text,
        "lemma":            token.lemma_, 
        "pos":              token.pos_, 
        "tag":              token.tag_,
        "dep":              token.dep_,
        "is_alpha":         token.is_alpha,
        "is_stop":          token.is_stop,
        "is_sent_start":    token.is_sent_start,
        "is_sent_end":      token.is_sent_end,
        "ent_type":         token.ent_type_,
        "ent_iob":          token.ent_iob_,
        "head_index":       token.head.i,
        "left_edge_index":  token.left_edge.i,
        "right_edge_index": token.right_edge.i,
        "norm":             token.norm_,
        "ent_kb":           token.ent_kb_id_,
        "morph":            str(token.morph),
        "whitespace":       token.whitespace_
    } for token in doc]
    
    noun_chunks = [{
        "text":           chunk.text,
        "start":          chunk.start,
        "root_text":      chunk.root.text, 
        "root_dep":       chunk.root.dep_,
        "root_head_text": chunk.root.head.text
    } for chunk in doc.noun_chunks]

    ents = [{
        "text":           entity.text,
        "id":             entity.id,
        "start":          entity.start,
        "ent_id":         entity.ent_id,
        "label":          entity.label_,
        "root_text":      entity.root.text,
        "root_dep":       entity.root.dep_,
        "root_head_text": entity.root.head.text
    } for entity in doc.ents]

    coref_clusters = [[{
        "text":           span.text, 
        "start":          span.start,
        "root_text":      span.root.text,
        "root_dep":       span.root.dep_,
        "root_head_text": span.root.head.text
    } for span in value] for (key, value) in doc.spans.items() if str(key).startswith("coref_clusters_")]

    parse_results.update({
        "tokens":         tokens,
        "noun_chunks":    noun_chunks,
        "entities":       ents,
        "coref_clusters": coref_clusters
    })

    return parse_results