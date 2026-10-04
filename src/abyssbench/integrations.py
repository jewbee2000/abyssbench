"""Optional OpenHTF attachment recipe, no station server or hardware dependency."""
import json


def attach_verdict(test_api, result, artifact_name='abyssbench-verdict.json'):
    """Call from an OpenHTF phase; attachment + phase outcome are the integration."""
    import openhtf

    test_api.attach(artifact_name, json.dumps(result, allow_nan=False), mimetype='application/json')
    return openhtf.PhaseResult.CONTINUE if result['status'] == 'pass' else openhtf.PhaseResult.FAIL_AND_CONTINUE
