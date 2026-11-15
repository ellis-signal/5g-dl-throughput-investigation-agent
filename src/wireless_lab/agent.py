"""Model-driven 5G investigation using an OpenAI-compatible local server."""
import argparse
import json
import math
import os
import time
import urllib.request
from pathlib import Path

if __package__:
    from .review import review
else:
    from review import review

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / 'data' / 'evaluation_cases.json'
SKILL = ROOT / 'skills' / '5g-dl-investigation' / 'SKILL.md'
URL = os.environ.get('MODEL_URL', 'http://127.0.0.1:18110/v1/chat/completions')
MODEL = os.environ.get('MODEL_NAME', 'local')


def load_case(case_id):
    for item in json.loads(CASES.read_text(encoding='utf-8')):
        if item['id'] == case_id:
            return {key: item[key] for key in ('id', 'bandwidth_mhz', 'baseline', 'incident')}
    raise ValueError('未知小区编号：' + case_id)


def compare_windows(case_id):
    case = load_case(case_id)
    before, after = case['baseline'], case['incident']
    delta = {}
    for key in ('rsrp_dbm_median', 'sinr_db_median', 'cqi_mean', 'prb_utilization_pct_mean', 'active_users_mean', 'dl_throughput_mbps_mean', 'bler_pct_mean', 'per_user_throughput_mbps'):
        a, b = before.get(key), after.get(key)
        delta[key] = round(b-a, 3) if a is not None and b is not None else None
    for metric, key in [('dl_throughput_mbps_mean', 'throughput_change_percent'),
                        ('active_users_mean', 'users_change_percent')]:
        base, current = before.get(metric), after.get(metric)
        delta[key] = round((current / base - 1) * 100, 2) if base and current is not None else None
    delta['missing'] = [key for key,value in delta.items() if value is None]
    return delta


def calculate_capacity(case_id):
    case = load_case(case_id)
    sinr = case['incident']['sinr_db_median']
    if sinr is None:
        raise ValueError('异常窗口缺少SINR，无法计算容量')
    capacity = case['bandwidth_mhz'] * math.log2(1 + 10 ** (sinr / 10))
    return {'bandwidth_mhz':case['bandwidth_mhz'], 'sinr_db':sinr, 'shannon_mbps':round(capacity,2), 'note':'单链路理想条件参考，不等于实际小区吞吐'}

TOOLS = {'get_kpi':load_case, 'compare_windows':compare_windows, 'calculate_capacity':calculate_capacity}
TOOL_SPECS = [
    {'type':'function','function':{'name':name,'description':description,'parameters':{'type':'object','properties':{'case_id':{'type':'string','description':'小区编号'}},'required':['case_id']}}}
    for name,description in [
        ('get_kpi','查询指定小区的基线和异常窗口KPI。'),
        ('compare_windows','计算两窗口的KPI变化及缺失字段。'),
        ('calculate_capacity','计算异常窗口理想香农容量参考值。')]
]


def ask_model(messages, tools=None):
    payload = {'model':MODEL,'messages':messages,'temperature':0,'max_tokens':900,'chat_template_kwargs':{'enable_thinking':False}}
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'
    request = urllib.request.Request(URL, data=json.dumps(payload,ensure_ascii=False).encode('utf-8'), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=180) as response:
        result=json.load(response)
    return result['choices'][0]['message'], result.get('usage',{})


def with_review(result):
    """Publish a deterministic review of actually returned tool data."""
    tools = {event['name']: event['result'] for event in result['trace']
             if event['kind'] == 'tool' and 'error' not in event['result']}
    if not {'get_kpi', 'compare_windows'} <= tools.keys():
        reviewed = {'label': 'INSUFFICIENT', 'reason': '缺少成功返回的KPI查询或窗口比较。',
                    'next_step': '检查工具配置并重新调查。', 'evidence': {}, 'hypotheses': {}}
    else:
        reviewed = review(tools['get_kpi'], tools['compare_windows'])
    return {**result, 'mode': 'D', 'model_answer': result['answer'], 'review': reviewed,
            'answer': json.dumps(reviewed, ensure_ascii=False, indent=2),
            'trace': [*result['trace'], {'kind': 'review', 'result': reviewed}]}


def run(case_id, mode='D', user_question=None):
    if mode == 'D':
        return with_review(run(case_id, 'C', user_question))
    start=time.perf_counter()
    case=load_case(case_id)
    trace=[]
    system='你是5G网络工程师。分析下行吞吐，结论标签只能是 COVERAGE、INTERFERENCE、CONGESTION、NORMAL、INSUFFICIENT。输出JSON，包含label、reason、support、counter、next_step。'
    if mode=='C':
        system += '\n' + SKILL.read_text(encoding='utf-8')
    question = f'{user_question} 当前小区编号：{case_id}。' if user_question else f'调查小区 {case_id} 的下行吞吐是否异常，比较可能原因并给出证据。'
    if mode=='A':
        question += '\n以下是可用的基线和异常窗口汇总：' + json.dumps(case,ensure_ascii=False)
    else:
        question += '可使用工具查询并计算。'
    messages=[{'role':'system','content':system},{'role':'user','content':question}]
    for _ in range(6):
        message, usage=ask_model(messages, TOOL_SPECS if mode!='A' else None)
        calls=message.get('tool_calls') or []
        trace.append({'kind':'model','content':message.get('content'),'tool_calls':calls,'usage':usage})
        messages.append(message)
        if not calls:
            return {'mode':mode,'case_id':case_id,'question':question,'answer':message.get('content') or '', 'trace':trace,'seconds':round(time.perf_counter()-start,2),'skill_loaded':mode=='C'}
        for call in calls:
            name=call['function']['name']
            try:
                args=json.loads(call['function']['arguments'])
                if name not in TOOLS or args.get('case_id') != case_id:
                    raise ValueError('工具或小区编号无效')
                result=TOOLS[name](case_id)
            except Exception as exc:
                result={'error':str(exc)}
            trace.append({'kind':'tool','name':name,'arguments':call['function']['arguments'],'result':result})
            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
    return {'mode':mode,'case_id':case_id,'question':question,'answer':'未在调用次数内完成调查','trace':trace,'seconds':round(time.perf_counter()-start,2),'skill_loaded':mode=='C'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',default='NR-CELL-1002')
    parser.add_argument('--mode',choices=['A','B','C','D'],default='D')
    parser.add_argument('--output')
    args=parser.parse_args()
    result=run(args.case,args.mode)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        Path(args.output).write_text(text,encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
