"""Scene-balanced summaries; no token/query pseudo-replication or PASS policy."""
def paired_interaction(conditions):
    names=('identity','delete_fine','delete_coarse')
    if any(conditions[name][group] is None for name in names for group in ('mixed','interior')):
        return None
    def excess(name):
        return ((conditions[name]['mixed']-conditions['identity']['mixed'])
                -(conditions[name]['interior']-conditions['identity']['interior']))
    return excess('delete_fine')-excess('delete_coarse')

def summarize(records):
    groups={}
    for row in records:
        value=paired_interaction(row['conditions'])
        key=(row['scene_id'],row['expression_index'])
        groups.setdefault(key,[])
        if value is not None:groups[key].append(value)
    expressions={key:sum(values)/len(values) if values else None for key,values in groups.items()}
    scenes={}
    for (scene,_),value in expressions.items():
        scenes.setdefault(scene,[])
        if value is not None:scenes[scene].append(value)
    values={scene:sum(items)/len(items) if items else None for scene,items in scenes.items()}
    valid=[value for value in values.values() if value is not None]
    return {'scene_interactions':values,'scene_balanced_mean':sum(valid)/len(valid) if valid else None,
            'scenes_with_readout':len(valid),'observed_scenes':len(scenes),
            'expressions_with_readout':sum(value is not None for value in expressions.values()),
            'observed_expressions':len(expressions),'matched_query_rows':len(records),
            'population_interval':None,'scientific_diagnosis_passed':False}
