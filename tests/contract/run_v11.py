#!/usr/bin/env python3
"""1.1 语义交接回归：合成契约输入，不证明模型选型质量或渲染质量。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / 'scripts/validate_plan.py'


def base(kind='echarts', cid='bar.rank'):
    details = {
        'echarts': {'mapping': {'category': 'team', 'value': 'hours'}, 'comparison_basis': '各团队实际工时，小时'},
        'table': {'columns': [{'field': 'team', 'label': '团队'}, {'field': 'hours', 'label': '工时'}], 'row_organization': '每团队一行，按名称排序', 'lookup_task': '查找具体团队工时'},
        'infographic': {'structure': {'steps': [{'label': '提交'}, {'label': '核验'}]}, 'relationship_semantics': '箭头表示操作顺序，不表示因果', 'reading_order': ['提交', '核验']},
        'text': {'text': '当前材料不足以推断因果'},
        'kpi': {'metric': 'hours', 'comparison_basis': '本月总工时', 'format': '小时，整数'},
    }
    spec = {'kind': kind, 'message': '呈现工作量或流程', 'evidence_refs': ['materials.csv'], 'boundaries': ['描述性结果'], **details[kind]}
    module = {'role': 'primary', 'capability_id': cid, 'question': '工作量或流程是什么', 'match': 'strong', 'rationale': '与当前读者任务相符', 'spec': spec,
              'carrier_adaptation': {'static': {'essential_information': '关键标签、单位和读数直接显示'}}}
    if kind in ('echarts', 'table', 'kpi'):
        module['bindings'] = [{'target': 'dataset.source', 'ref': {'type': 'file', 'id': 'materials.csv'}, 'expects': 'array<object>', 'required_fields': ['team', 'hours']}]
    return {'contract_version': '1.1', 'output_level': 'decision', 'mode': 'api', 'status': 'ok', 'summary': '工作量呈现方案',
            'echarts': {'version': '6.1.0', 'deps': [], 'renderer': 'svg'}, 'intent': {'goal': '看工作量', 'scenario': 'executive', 'inferred': False, 'confidence': 'high'},
            'data': {'ref': {'type': 'file', 'id': 'materials.csv'}, 'profile': {'rows': 2, 'dimensions': ['team'], 'measures': ['hours']},
                     'binding': {'mode': 'dataset.source', 'expects': 'array<object>', 'required_fields': ['team', 'hours']}, 'transform_policy': 'propose'},
            'constraints': {'static': True, 'offline': True}, 'plan': [module]}


def main():
    cases = []
    def case(name, expected=True, plan=None, edit=None):
        plan = copy.deepcopy(plan if plan is not None else base())
        if edit: edit(plan)
        cases.append((name, expected, plan))
    case('decision 无 option')
    for kind, cid in [('table', 'table.detail'), ('text', 'text.conclusion'), ('infographic', 'infographic'), ('kpi', 'kpi.card')]:
        case(kind + ' 完整规格', plan=base(kind, cid))
    for cid in ('infographic.process', 'infographic.swimlane', 'infographic.mechanism', 'infographic.journey', 'infographic.capability', 'infographic.condition', 'infographic.dependency'):
        case(cid + ' 完整开放语义规格', plan=base('infographic', cid))
        case(cid + ' 错 kind', False, edit=lambda p, c=cid: p['plan'][0].update(capability_id=c))
    case('哑铃 decision', edit=lambda p: p['plan'][0].update(capability_id='comparison.dumbbell'))
    case('坡度 decision', edit=lambda p: p['plan'][0].update(capability_id='comparison.slope'))
    case('implementation option', edit=lambda p: (p.update(output_level='implementation'), p['plan'][0].update(option={'series': [{'type': 'bar'}]})))
    case('implementation 缺省仍需 option', False, edit=lambda p: p.pop('output_level'))
    case('1.0 禁止 decision', False, edit=lambda p: p.update(contract_version='1.0'))
    case('缺 mapping', False, edit=lambda p: p['plan'][0]['spec'].pop('mapping'))
    case('空 table columns', False, plan=base('table', 'table.detail'), edit=lambda p: p['plan'][0]['spec'].update(columns=[]))
    case('空 infographic structure', False, plan=base('infographic', 'infographic'), edit=lambda p: p['plan'][0]['spec'].update(structure={}))
    case('空 reading_order', False, plan=base('infographic', 'infographic'), edit=lambda p: p['plan'][0]['spec'].update(reading_order=[]))
    case('空 text', False, plan=base('text', 'text.conclusion'), edit=lambda p: p['plan'][0]['spec'].update(text=''))
    case('类型与 capability 错配', False, edit=lambda p: p['plan'][0].update(capability_id='table.detail'))
    case('缺 bindings', False, edit=lambda p: p['plan'][0].pop('bindings'))
    case('绑定缺 ref', False, edit=lambda p: p['plan'][0]['bindings'][0].pop('ref'))
    case('static 缺可读方案', False, edit=lambda p: p['plan'][0].pop('carrier_adaptation'))
    case('空嵌套结构', False, plan=base('infographic', 'infographic'), edit=lambda p: p['plan'][0]['spec'].update(structure={'steps': []}))
    case('空 series 不崩溃', False, edit=lambda p: p['plan'][0].update(option={'series': None}))
    case('decision 扩展也需依赖', False, edit=lambda p: p['plan'][0].update(capability_id='ext.violin'))
    def extension(p, dependency='@echarts-x/custom-violin@1.1.1', cid='ext.violin'):
        p['plan'][0]['capability_id'] = cid
        p['echarts']['deps'] = [dependency]
    case('decision 正确扩展版本', edit=extension)
    case('同前缀错误扩展包', False, edit=lambda p: extension(p, '@echarts-x/custom-contour@1.2.1'))
    case('扩展错误版本', False, edit=lambda p: extension(p, '@echarts-x/custom-violin@0.0.1'))
    case('显式禁止扩展', False, edit=lambda p: (extension(p), p['constraints'].update(allow_extensions=False)))
    case('扩展运行时不可用', False, edit=lambda p: (extension(p), p['constraints'].update(runtime={'available_dependencies': []})))
    case('3D 显式许可可用', edit=lambda p: (extension(p, 'echarts-gl@2.1.0', 'gl.bar3d'), p['constraints'].update(allow_3d=True)))
    case('3D 显式禁止', False, edit=lambda p: (extension(p, 'echarts-gl@2.1.0', 'gl.bar3d'), p['constraints'].update(allow_3d=False)))
    case('错误结构不崩溃', False, edit=lambda p: p.update(echarts=[]))
    case('缺失 assumptions', False, edit=lambda p: p.update(status='ok_with_assumptions'))
    case('非法 transform_policy', False, edit=lambda p: p['data'].update(transform_policy='overwrite'))
    case('函数字符串不是 renderItem', False, edit=lambda p: (p['plan'][0].update(capability_id='custom.custom', option={'series': [{'type': 'custom', 'renderItem': 'function () {}'}]})))
    case('错误 series', False, edit=lambda p: p['plan'][0].update(option={'series': [{'type': 'pie'}]}))
    case('超过本体6KB', False, edit=lambda p: p.update(summary='信息' * 2000))
    case('无行级数据回传', False, edit=lambda p: p['data'].update(inline=[{'hours': 12}]))
    with tempfile.TemporaryDirectory(prefix='viz-contract-') as tmp:
        tmp = Path(tmp)
        spec = base('infographic', 'infographic')['plan'][0]['spec']
        spec['structure']['explanation'] = '详细规格' * 2000
        (tmp / 'detail.json').write_text(json.dumps(spec, ensure_ascii=False))
        referenced = base('infographic', 'infographic')
        referenced['plan'][0].pop('spec')
        referenced['plan'][0]['spec_ref'] = {'path': 'detail.json'}
        case('可读大规格引用不算本体', plan=referenced)
        case('绝对规格引用', plan=referenced, edit=lambda p: p['plan'][0]['spec_ref'].update(path=str(tmp / 'detail.json')))
        case('缺失引用', False, plan=referenced, edit=lambda p: p['plan'][0]['spec_ref'].update(path='missing.json'))
        (tmp / 'bad.json').write_text('{"kind":"infographic"}')
        case('引用缺语义', False, plan=referenced, edit=lambda p: p['plan'][0]['spec_ref'].update(path='bad.json'))
        (tmp / 'invalid.json').write_text('not json')
        case('非 JSON 引用', False, plan=referenced, edit=lambda p: p['plan'][0]['spec_ref'].update(path='invalid.json'))
        for label, value in [('null', None), ('false', False), ('array', []), ('scalar', 'not a spec')]:
            filename = f'value-{label}.json'
            (tmp / filename).write_text(json.dumps(value))
            case(f'规格引用 {label} 不可跳过语义', False, plan=referenced,
                 edit=lambda p, f=filename: p['plan'][0]['spec_ref'].update(path=f))
            case(f'实现引用 {label} 不可跳过语义', False,
                 edit=lambda p, f=filename: (p.update(output_level='implementation'), p['plan'][0].update(implementation_ref={'path': f})))
        (tmp / 'implementation.json').write_text(json.dumps({'option': {'series': [{'type': 'bar'}]}}))
        case('实现引用', edit=lambda p: (p.update(output_level='implementation'), p['plan'][0].update(implementation_ref={'path': 'implementation.json'})))
        failed = []
        for name, expected, plan in cases:
            path = tmp / 'plan.json'; path.write_text(json.dumps(plan, ensure_ascii=False))
            outcomes = []
            for flags in (['--schema'], ['--schema', '--builtin-only']):
                result = subprocess.run([sys.executable, str(VALIDATOR), str(path), *flags], text=True, capture_output=True)
                outcomes.append(result.returncode == 0)
                if 'Traceback' in result.stderr or (result.returncode == 0) != expected:
                    failed.append((name, flags, result.stdout, result.stderr))
            print(f'{name}: {"PASS" if outcomes == [expected, expected] else "FAIL"}')
        print(f'{len(cases)} cases × 2 validator paths; {len(failed)} failures')
        for failure in failed: print(failure)
        return bool(failed)

if __name__ == '__main__':
    raise SystemExit(main())
