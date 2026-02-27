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
      label: 'Data requirements',
      collapsed: false,
      items: [
        'data-requirements/cnv',
        'data-requirements/genes',
        'data-requirements/other',

      ],
    },
    {
      type: 'category',
      label: 'How to validate your data',
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
          href: 'https://github.com/ebispot/gwas-pysumstats',
        },
      ],
    },
    'how-to-submit',
  ],
};

export default sidebars;
