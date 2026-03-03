import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'I want to submit data',
      collapsed: false,
      items: [
        'how-to-submit',
        {
          type: 'category',
          label: 'Data requirements',
          collapsed: false,
          items: [
            'data_requirements/cnv',
            'data_requirements/genes',
            'data_requirements/other',
          ],
        },
        {
          type: 'category',
          label: 'Validate your data',
          collapsed: false,
          items: [
            {
              type: 'link',
              label: 'Use your web browser',
              href: 'pathname:///validate/',
            },
            {
              type: 'link',
              label: 'Bulk processing with the CLI',
              href: 'https://github.com/ebispot/gwas-beyond-snps',
            },
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'I want to reuse data',
      collapsed: true,
      items: [
        'how-to-reuse',
        {
          type: 'category',
          label: 'Architecture decision records',
          collapsed: true,
          items: [
            'decision_records/cnv',
            'decision_records/genes',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
