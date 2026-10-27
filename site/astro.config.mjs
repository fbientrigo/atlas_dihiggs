import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://fbientrigo.github.io',
  base: process.env.BASE_PATH || '/',
  integrations: [
    starlight({
      title: 'ATLAS // DIHIGGS',
      description: 'Documentation & API Reference for 2HDM DiHiggs & LLP Recast Workspace',
      customCss: ['./src/styles/wired.css'],
      social: {
        github: 'https://github.com/fbientrigo/atlas_dihiggs',
      },
      sidebar: [
        {
          label: '[00] OVERVIEW',
          items: [
            { label: 'Introduction', link: '/' },
            { label: 'Getting Started', link: '/getting-started/' },
            { label: 'Scientific Pipeline', link: '/pipeline/' },
          ],
        },
        {
          label: '[01] MODULES',
          items: [
            { label: 'Architecture Overview', link: '/modules/' },
            { label: 'dihiggs (Theory)', link: '/modules/dihiggs/' },
            { label: 'dihiggs_ufo (UFO & Pythia)', link: '/modules/dihiggs-ufo/' },
            { label: 'dihiggs_hep_cross (MadGraph)', link: '/modules/dihiggs-hep-cross/' },
            { label: 'dihiggs_llp_recast (DV+jets)', link: '/modules/dihiggs-llp-recast/' },
            { label: 'dihiggs_boundary (Integration)', link: '/modules/dihiggs-boundary/' },
            { label: 'recast_viewer (Visualization)', link: '/modules/recast-viewer/' },
          ],
        },
        {
          label: '[02] GOVERNANCE',
          items: [
            { label: 'Physics Authority & Provenance', link: '/authority/' },
            { label: 'Data Lake Architecture', link: '/lake/' },
          ],
        },
        {
          label: '[03] API REFERENCE',
          items: [
            { label: 'API Overview & Coverage', link: '/api/' },
            {
              label: '2HDMC (C++ Base)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/base/2hdmc' },
            },
            {
              label: 'HiggsTools (C++ Base)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/base/higgstools' },
            },
            {
              label: 'dihiggs (C++)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/project/dihiggs' },
            },
            {
              label: 'dihiggs_boundary (C++)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/project/boundary' },
            },
            {
              label: 'dihiggs_hep_cross (C++)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/project/hep_cross' },
            },
            {
              label: 'dihiggs_llp_recast (C++)',
              collapsed: true,
              autogenerate: { directory: 'api/cpp/project/llp_recast' },
            },
            {
              label: 'dihiggs (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/dihiggs' },
            },
            {
              label: 'dihiggs_boundary (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/dihiggs-boundary' },
            },
            {
              label: 'dihiggs_hep_cross (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/dihiggs-hep-cross' },
            },
            {
              label: 'dihiggs_llp_recast (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/dihiggs-llp-recast' },
            },
            {
              label: 'dihiggs_ufo (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/dihiggs-ufo' },
            },
            {
              label: 'recast_viewer (Python)',
              collapsed: true,
              autogenerate: { directory: 'api/python/recast-viewer' },
            },
          ],
        },
      ],
    }),
  ],
});
