"""Outcome-blind donor choice and scene-balanced conditional effects."""
def select_donors(cohort):
    rows=[]
    for scene in cohort:
        begin=len(rows)
        for expression in scene['expression_ids']:
            rows.append({'scene_id':scene['scene_id'],**expression,'scene_begin':begin,'scene_size':len(scene['expression_ids'])})
    donors={}
    for index,row in enumerate(rows):
        within=index-row['scene_begin']
        donors[index]=next((row['scene_begin']+(within+shift)%row['scene_size']
                            for shift in range(1,row['scene_size'])
                            if rows[row['scene_begin']+(within+shift)%row['scene_size']]['object_id']!=row['object_id']),None)
    return rows,donors

def summarize(records):
    expressions={}
    for row in records:
        key=(row['scene_id'],row['expression_index'])
        expressions.setdefault(key,[])
        if row.get('donor_minus_own_probability_error') is not None:
            expressions[key].append(row['donor_minus_own_probability_error'])
    scenes={}
    for (scene,_),values in expressions.items():
        scenes.setdefault(scene,[])
        if values:scenes[scene].append(sum(values)/len(values))
    effects={scene:sum(values)/len(values) if values else None for scene,values in scenes.items()}
    observed=[value for value in effects.values() if value is not None]
    return {'scene_effects':effects,'scene_balanced_effect':sum(observed)/len(observed) if observed else None,
            'observed_scenes':len(scenes),'scenes_with_readout':len(observed),
            'observed_expressions':len(expressions),'expressions_with_readout':sum(bool(v) for v in expressions.values()),
            'matched_query_rows':sum(row.get('native_query') is not None for row in records),
            'population_interval':None,'scientific_diagnosis_passed':False}
