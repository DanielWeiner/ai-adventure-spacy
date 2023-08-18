from spacy import Language

def parse(nlp: Language, nlp_coref: Language, value: str) -> str:
    tokens = []
    noun_chunks = []
    ents = []
    coref_clusters = []
    
    if isinstance(value, str):
        doc = nlp(value)
        doc = nlp_coref(doc)
        
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
    return {
        "tokens":         tokens,
        "noun_chunks":    noun_chunks,
        "entities":       ents,
        "coref_clusters": coref_clusters
    }
