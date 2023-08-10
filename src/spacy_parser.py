from spacy import Language
import json

def parse(nlp: Language, value: str) -> str:
    doc = nlp(value)
    
    tokens = [{
            "index":            token.i,
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
            "head_text":        token.head.text,
            "left_edge_index":  token.left_edge.i,
            "left_edge_text":   token.left_edge.text,
            "right_edge_index": token.right_edge.i,
            "right_edge_text":  token.right_edge.text,
            "norm":             token.norm_,
            "ent_kb":           token.ent_kb_id_,
            "morph":            str(token.morph)
        } for token in doc]
    
    noun_chunks = [{
        "text":           chunk.text, 
        "root_text":      chunk.root.text, 
        "root_dep":       chunk.root.dep_,
        "root_head_text": chunk.root.head.text
    } for chunk in doc.noun_chunks]

    ents = [{
        "text":   entity.text,
        "id":     entity.id,
        "ent_id": entity.ent_id,
        "label":  entity.label_
    } for entity in doc.ents]

    return json.dumps({
        "tokens":      tokens,
        "noun_chunks": noun_chunks,
        "entities":    ents
    })