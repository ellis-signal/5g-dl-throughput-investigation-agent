"""Deterministic test plan, NOT a substitute for DSH model `skill` calls."""
PLAN_TEMPLATES = {
    'single': [('wireless-capacity-code', 'capacity')],
    'branch': [('wireless-link-branch', 'route')],
    'batch': [('wireless-link-workflow', 'validate'), ('wireless-link-workflow', 'compute'), ('wireless-link-workflow', 'verify')],
    'batch-audit': [('wireless-link-workflow', 'validate'), ('wireless-link-workflow', 'compute'), ('wireless-link-workflow', 'verify'), ('wireless-capacity-audit', 'audit')],
    'batch-audit-diagnose': [('wireless-link-workflow', 'validate'), ('wireless-link-workflow', 'compute'), ('wireless-link-workflow', 'verify'), ('wireless-capacity-audit', 'audit'), ('wireless-ops-diagnosis', 'read-reference')],
}


def plan(task):
    steps = PLAN_TEMPLATES[task]
    return {
        'task_type': task,
        'kind': 'EXPECTED_PLAN_ONLY_NOT_AN_EXECUTION_TRACE',
        'skill_loads': list(dict.fromkeys(skill for skill, _ in steps)),
        'steps': [{'skill': skill, 'action': action} for skill, action in steps],
    }
