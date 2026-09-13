"""Offline checks for shipped YAML/Jinja. No HA connection and no notifications."""
from pathlib import Path
from types import SimpleNamespace
from dataclasses import dataclass, field
from copy import deepcopy
import ast
import math
import yaml
from jinja2 import StrictUndefined
from jinja2.nativetypes import NativeEnvironment
from jinja2.sandbox import ImmutableSandboxedEnvironment

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class Input:
    name: str

class Loader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    result = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        assert key not in result, f'Duplicate YAML key: {key}'
        result[key] = loader.construct_object(v, deep=deep)
    return result

Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
Loader.add_constructor('!input', lambda loader, node: Input(loader.construct_scalar(node)))

class NativeSandbox(ImmutableSandboxedEnvironment, NativeEnvironment):
    pass

ENV = NativeSandbox(undefined=StrictUndefined)

def render(value, scope):
    if isinstance(value, dict):
        return {k: render(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [render(v, scope) for v in value]
    if not isinstance(value, str) or ('{{' not in value and '{%' not in value):
        return value
    result = ENV.from_string(value).render(**scope)
    if isinstance(result, str):
        try:
            return ast.literal_eval(result.strip())
        except (ValueError, SyntaxError):
            return result.strip()
    return result

def substitute(value, inputs):
    if isinstance(value, Input):
        assert value.name in inputs, f'Undefined input: {value.name}'
        return deepcopy(inputs[value.name])
    if isinstance(value, dict):
        return {k: substitute(v, inputs) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, inputs) for v in value]
    return value

def compile_templates(value):
    if isinstance(value, str) and ('{{' in value or '{%' in value):
        ENV.from_string(value)
    elif isinstance(value, dict):
        for child in value.values():
            compile_templates(child)
    elif isinstance(value, list):
        for child in value:
            compile_templates(child)

def load_blueprint(name, overrides=None):
    data = yaml.load((ROOT / 'blueprints/automation/satel' / name).read_text(), Loader)
    assert data['blueprint']['domain'] == 'automation'
    assert data['blueprint']['source_url'].endswith('/' + name)
    inputs = {k: v['default'] for k, v in data['blueprint']['input'].items()}
    inputs.update(overrides or {})
    result = substitute({k:v for k,v in data.items() if k != 'blueprint'}, inputs)
    compile_templates(result)
    assert 'automation' not in result and 'template' not in result and 'input_boolean' not in result
    return result

@dataclass
class State:
    entity_id: str
    state: str
    attributes: dict = field(default_factory=dict)
    age: float = 120

class States:
    def __init__(self, values):
        self.values = {s.entity_id:s for s in values}
    def __call__(self, entity):
        return self.values.get(entity, State(entity,'unknown')).state
    def __getattr__(self, domain):
        return [s for s in self.values.values() if s.entity_id.startswith(domain + '.')]
    def attr(self, entity, attr):
        return self.values.get(entity, State(entity,'unknown')).attributes.get(attr)

READY = 'input_boolean.satel_powiadomienia_gotowe'
MEMORY = 'sensor.satel_powiadomienia_pamiec'
CONN = 'binary_sensor.satel_powiadomienia_lacznosc'
LATCH = 'input_boolean.satel_powiadomienia_awaria_lacznosci'

# Minimal evaluator for actual template/condition/action fields, not a HA runtime.
def condition(item, scope):
    if item['condition'] == 'template':
        return bool(render(item['value_template'], scope))
    assert item['condition'] == 'state', item
    state = scope['states'].values.get(item['entity_id'])
    return bool(state and state.state == item['state'] and state.age >= item.get('for',{}).get('seconds',0))

def sequence(actions, scope, calls):
    for a in actions:
        if not render(a.get('enabled',True),scope):
            continue
        if 'variables' in a:
            for k,v in a['variables'].items():
                scope[k] = render(v,scope)
        elif 'condition' in a:
            if not condition(a,scope):
                return
        elif 'choose' in a:
            for choice in a['choose']:
                if all(condition(c,scope) for c in choice['conditions']):
                    sequence(choice['sequence'],scope,calls)
                    break
            else:
                sequence(a.get('default',[]),scope,calls)
        elif 'if' in a:
            branch = 'then' if all(condition(c,scope) for c in a['if']) else 'else'
            sequence(a.get(branch,[]),scope,calls)
        elif 'sequence' in a:
            sequence(a['sequence'],scope,calls)
        elif 'action' in a:
            calls.append((render(a['action'],scope), render(a.get('data',{}),scope)))
            if a['action'].startswith('input_boolean.'):
                entity = a['target']['entity_id']
                scope['states'].values[entity].state = 'on' if a['action'].endswith('turn_on') else 'off'
        else:
            raise AssertionError(a)

def execute(bp, values, trigger=None, manual=False):
    states = States(deepcopy(values))
    scope = {'states':states,'state_attr':states.attr}
    if trigger is not None:
        scope['trigger'] = trigger
    for k,v in bp.get('variables',{}).items():
        scope[k] = render(v,scope)
    calls = []
    if manual or all(condition(c,scope) for c in bp.get('conditions',[])):
        sequence(bp['actions'],scope,calls)
    return calls, states

def memory(active, **extra):
    return State(MEMORY,'monitoring',dict(schema='satel_notifications_v1',active=active,**extra))

def record(name):
    return {'name':name,'entity_id':'sensor.test','category':'trouble'}

def delta(before,after):
    return SimpleNamespace(from_state=memory(before),to_state=memory(after))

alarm = load_blueprint('satel_alarm_notifications.yaml')
conn = load_blueprint('satel_connectivity_notifications.yaml')
assert alarm['mode']=='queued' and alarm['max']==100
assert conn['mode']=='single'
old = {'trouble:A':record('Awaria A'),'trouble:B':record('Awaria B')}
new = {'trouble:A':record('Awaria A'),'trouble:C':record('Awaria C')}
ready = [State(READY,'on')]
calls,_ = execute(alarm,ready,delta(old,new))
assert len(calls)==2 and calls[0][0]=='persistent_notification.create'
assert calls[1][0]=='notify.mobile_app_s24_ultra'
assert 'Awaria B' in calls[1][1]['message'] and 'Awaria C' in calls[1][1]['message']
assert 'Awaria A' not in calls[1][1]['message']
assert not execute(alarm,ready,delta(new,new))[0]
assert not execute(alarm,[State(READY,'off')],delta(old,new))[0]
assert not execute(alarm,ready,manual=True)[0]
assert not execute(alarm,ready,SimpleNamespace(),manual=True)[0]
for bad in [SimpleNamespace(from_state=None,to_state=memory(new)),
            SimpleNamespace(from_state=memory(old),to_state=memory(new,restored=True)),
            SimpleNamespace(from_state=memory(old),to_state=State(MEMORY,'unknown'))]:
    assert not execute(alarm,ready,bad)[0]
no_recovery = load_blueprint('satel_alarm_notifications.yaml',{'send_recovery':False})
calls,_ = execute(no_recovery,ready,delta(old,new))
assert 'Awaria B' not in calls[-1][1]['message'] and 'Awaria C' in calls[-1][1]['message']
assert not execute(no_recovery,ready,delta(old,{}))[0]
mobile_off = load_blueprint('satel_alarm_notifications.yaml',{'mobile_enabled':False})
assert [c[0] for c in execute(mobile_off,ready,delta(old,new))[0]]==['persistent_notification.create']
custom = load_blueprint('satel_alarm_notifications.yaml',{'memory_entity':'sensor.custom_memory','mobile_actions':[
    {'action':'notify.test_1','data':{'title':'{{ notification_title }}','message':'{{ notification_message }}'}},
    {'action':'notify.test_2','data':{'title':'{{ notification_title }}','message':'{{ notification_message }}'}}]})
calls,_ = execute(custom,ready,delta(old,new))
assert calls[0][1]['notification_id'].endswith('sensor_custom_memory')
assert [c[0] for c in calls[1:]]==['notify.test_1','notify.test_2']
assert calls[1][1]==calls[2][1]

source = State('binary_sensor.satel_source','off',{'satel_gateway':'integra_test'})
def connectivity_values(state='off',latch='off',sources=(),age=120,gateway='integra_test'):
    return [State(READY,'on',age=age),State(CONN,state,{'gateway_id':gateway}),State(LATCH,latch),*sources]

calls,states = execute(conn,connectivity_values())
assert [c[0] for c in calls]==['persistent_notification.create','notify.mobile_app_s24_ultra','input_boolean.turn_on']
assert states(LATCH)=='on'
assert not execute(conn,connectivity_values(latch='on'))[0]
assert not execute(conn,connectivity_values(age=49))[0]
assert not execute(conn,connectivity_values(sources=[source]))[0]
assert not execute(conn,connectivity_values(gateway='wrong'))[0]
assert not execute(conn,connectivity_values(state='on',latch='on'))[0]
calls,states = execute(conn,connectivity_values(state='on',latch='on',sources=[source]))
assert states(LATCH)=='off' and calls[-1][0]=='input_boolean.turn_off'
assert len([c for c in calls if c[0].startswith('notify.')])==1
no_recovery = load_blueprint('satel_connectivity_notifications.yaml',{'send_recovery':False})
calls,states = execute(no_recovery,connectivity_values(state='on',latch='on',sources=[source]))
assert states(LATCH)=='off'
assert not any(c[0]=='persistent_notification.create' or c[0].startswith('notify.') for c in calls)
assert any(c[0]=='persistent_notification.dismiss' for c in calls)

base = yaml.load((ROOT/'packages/satel_notifications_base.yaml').read_text(),Loader)
compile_templates(base)
assert set(base)=={'input_boolean','template','automation'}
assert len(base['automation'])==1 and base['automation'][0]['id']=='satel_notifications_startup_v1'
assert base['input_boolean']['satel_powiadomienia_gotowe']['initial'] is False
assert 'initial' not in base['input_boolean']['satel_powiadomienia_awaria_lacznosci']
assert base['template'][0]['sensor'][0]['unique_id']=='satel_notifications_memory_v1'
assert base['template'][1]['binary_sensor'][0]['delay_off']=='00:01:00'
assert base['template'][1]['binary_sensor'][0]['attributes']['gateway_id']=='integra_test'
assert 'notify.' not in (ROOT/'packages/satel_notifications_base.yaml').read_text()
print('PASS: YAML/input substitution, Jinja, exact same-count changes, no recovery mode, manual/restore guards, custom actions, outage/recovery/live-source guards, startup grace, shared base IDs.')
print('Offline checks only; no Home Assistant runtime, no notification delivery.')
