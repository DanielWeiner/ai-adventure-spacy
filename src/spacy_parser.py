from concurrent.futures import Future
from src.fixed_dict import FixedDict
from spacy import Language
from amrlib.alignments.faa_aligner import FAA_Aligner
from amrlib.models.inference_bases import STOGInferenceBase
import penman
from penman.surface import AlignmentMarker

parse_result_defaults = {
    "tokens":         [],
    "noun_chunks":    [],
    "entities":       [],
    "coref_clusters": [],
    "amr_graphs":     []
}

class ParseResults(FixedDict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(parse_result_defaults.keys(), *args, **kwargs)

def parse(nlp_future: Future[tuple[Language, STOGInferenceBase]], value: str):
    parse_results = ParseResults(parse_result_defaults)
    
    if not isinstance(value, str) or len(value) == 0:
        return parse_results
    
    nlp, amr_model = nlp_future.result()
    doc = nlp(value)

    sents = [ sent.text for sent in doc.sents ]
    sent_token_indices = [ [ tok.i for tok in sent ] for sent in doc.sents ]
    sents_tokenized = [ " ".join([ tok.text for tok in sent ]) for sent in doc.sents ]
    graphs : list[str] = amr_model.parse_sents(sents)
    aligner = FAA_Aligner()
    amr_surface_aligns, alignment_strings = aligner.align_sents(sents_tokenized, graphs)

    graphs = []
    for i, graph in enumerate(amr_surface_aligns):
        g = penman.decode(graph)
        triples = [ { "source": source, "role": role, "target": target } for (source, role, target) in g.triples ]
        epidata = [ { "triple": { "source": source, "role": role, "target": target }, "epidata": [ 
            { 
                "mode": epidatum.mode, 
                "type": type(epidatum).__name__,
                "repr": epidatum.__repr__(),
                "annotations": { 
                    slot: epidatum.__getattribute__(slot) for slot in epidatum.__slots__
                } if not isinstance(epidatum, AlignmentMarker) else {
                    "indices": [ index for index in epidatum.indices ],
                    "prefix": epidatum.prefix
                }
            } for epidatum in e ] } for ((source, role, target), e ) in g.epidata.items() ]
        graphs.append({
            "graph":         graph,
            "token_indices": sent_token_indices[i],
            "alignments":    alignment_strings[i],
            "triples":       triples,
            "epidata":       epidata,
            "metadata":      g.metadata
        })
    
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
        "coref_clusters": coref_clusters,
        "amr_graphs":     graphs
    })

    return parse_results