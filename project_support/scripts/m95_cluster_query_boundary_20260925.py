"""Validate a selected expression's opt-in cluster/query boundary trace."""


def boundary_trace_record(events, expected_layers, point_count, query_count):
    if len(events) != len(expected_layers):
        raise ValueError("Incomplete encoder boundary trace")
    record = []
    for expected, event in zip(expected_layers, events):
        if event["layer"] != expected:
            raise ValueError("Encoder boundary layer order differs")
        for key in ("cluster_input", "cluster_message", "readback", "decoder_points"):
            if key not in event:
                raise ValueError("Incomplete %s boundary" % key)
            if len(event[key]) != point_count:
                raise ValueError("%s support differs" % key)
        for key in ("decoder_query_input", "decoder_query_output"):
            if key not in event:
                raise ValueError("Incomplete %s boundary" % key)
            if len(event[key]) != query_count:
                raise ValueError("%s query axis differs" % key)
        if len(event["cluster_input"][0]) != len(event["cluster_message"][0]):
            raise ValueError("Cluster feature width differs")
        if len(event["readback"][0]) != len(event["decoder_points"][0]):
            raise ValueError("Readback feature width differs")
        record.append(event)
    return {"contract": "m95_cluster_query_boundary_v1", "layers": record}
