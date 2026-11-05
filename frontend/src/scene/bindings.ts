// СГЕНЕРИРОВАНО из backend/src/factoria/tags/registry.yaml.
// Не редактировать вручную: python scripts/gen-bindings.py

export type BindingMode = 'spin' | 'heat' | 'visibility' | 'label';

export interface Binding {
  mesh: string;
  tag: TagId;
  mode: BindingMode;
}

export const TAGS = [
  'L1.Running',
  'L1.Speed.SP',
  'L1.Speed.PV',
  'L1.Temp.PV',
  'L1.Load.Pct',
  'L1.Alarm.Code',
  'L1.Recipe.ID',
  'L2.Running',
  'L2.Speed.SP',
  'L2.Speed.PV',
  'L2.Temp.PV',
  'L2.Load.Pct',
  'L2.Alarm.Code',
  'L2.Recipe.ID',
  'L3.Running',
  'L3.Speed.SP',
  'L3.Speed.PV',
  'L3.Temp.PV',
  'L3.Load.Pct',
  'L3.Alarm.Code',
  'L3.Recipe.ID',
] as const;

export type TagId = (typeof TAGS)[number];

export const BINDINGS: Binding[] = [
  { mesh: 'L1.indicator', tag: 'L1.Running', mode: 'visibility' },
  { mesh: 'L1.rotor', tag: 'L1.Speed.PV', mode: 'spin' },
  { mesh: 'L1.body', tag: 'L1.Temp.PV', mode: 'heat' },
  { mesh: 'L1.label', tag: 'L1.Load.Pct', mode: 'label' },
  { mesh: 'L2.indicator', tag: 'L2.Running', mode: 'visibility' },
  { mesh: 'L2.rotor', tag: 'L2.Speed.PV', mode: 'spin' },
  { mesh: 'L2.body', tag: 'L2.Temp.PV', mode: 'heat' },
  { mesh: 'L2.label', tag: 'L2.Load.Pct', mode: 'label' },
  { mesh: 'L3.indicator', tag: 'L3.Running', mode: 'visibility' },
  { mesh: 'L3.rotor', tag: 'L3.Speed.PV', mode: 'spin' },
  { mesh: 'L3.body', tag: 'L3.Temp.PV', mode: 'heat' },
  { mesh: 'L3.label', tag: 'L3.Load.Pct', mode: 'label' },
];
