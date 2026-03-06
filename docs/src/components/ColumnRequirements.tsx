import React from 'react';
import columnDefs from '../../../src/gwascatalog/sumstatapp/web/column-defs.json';

type VariationType = 'gene' | 'cnv';

interface Column {
  code: string;
  description: string;
  form?: Record<string, string>;
}

interface ColumnGroup {
  id: string;
  label: string;
  hint?: string;
  note?: string;
  requirement: string;
  requirementDetail?: string;
  selectionRule: string;
  columns: Column[];
  errors?: { id: string; message: string }[];
  hasPrimarySelection?: boolean;
}

interface VariationDef {
  label: string;
  minimumRows: number;
  groups: ColumnGroup[];
}

interface ValidationRule {
  id: string;
  summary: string;
  detail: string;
  appliesTo: string[];
}

interface ColumnDefsData {
  gene: VariationDef;
  cnv: VariationDef;
  validationRules: ValidationRule[];
}

const defs = columnDefs as ColumnDefsData;

const REQUIREMENT_STYLES: Record<string, string> = {
  mandatory: 'badge badge--danger',
  optional: 'badge badge--info',
  conditional: 'badge badge--warning',
};

const REQUIREMENT_LABELS: Record<string, string> = {
  mandatory: 'Required',
  optional: 'Optional',
  conditional: 'Conditional',
};

const SELECTION_LABELS: Record<string, string> = {
  exactlyOne: 'select one',
  all: 'all fields required',
  atLeastOne: 'at least one required',
  allOrNone: 'all or none',
  any: '',
};

interface Props {
  /** Which variation type to render requirements for. */
  type: VariationType;
}

/**
 * Renders column requirements for a variation type from the shared
 * column-defs.json file. Used in data requirements documentation pages.
 */
export default function ColumnRequirements({ type }: Props): React.JSX.Element {
  const typeDef = defs[type];
  const rules = defs.validationRules.filter((r) => r.appliesTo.includes(type));

  return (
    <div>
      {typeDef.groups.map((group) => (
        <section key={group.id} style={{ marginBottom: '1.5rem' }}>
          <h3>{group.label}</h3>
          <p>
            <span className={REQUIREMENT_STYLES[group.requirement]}>
              {REQUIREMENT_LABELS[group.requirement]}
            </span>
            {SELECTION_LABELS[group.selectionRule] && (
              <> &mdash; {SELECTION_LABELS[group.selectionRule]}</>
            )}
          </p>
          {group.hint && <p>{group.hint}</p>}
          {group.requirementDetail && (
            <p>
              <em>{group.requirementDetail}</em>
            </p>
          )}
          <table>
            <thead>
              <tr>
                <th>Column</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {group.columns.map((col) => (
                <tr key={col.code}>
                  <td>
                    <code>{col.code}</code>
                  </td>
                  <td>{col.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {group.note && (
            <p>
              <em>{group.note}</em>
            </p>
          )}
        </section>
      ))}

      <section>
        <h3>Validation rules</h3>
        <p>
          These rules are enforced during validation. The same rules apply in
          both the web tool and the command line interface.
        </p>
        <ul>
          {rules.map((rule) => (
            <li key={rule.id}>
              <strong>{rule.summary}:</strong> {rule.detail}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
