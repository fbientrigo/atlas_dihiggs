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
              label: 'C++ Base Libraries',
              autogenerate: { directory: 'api/cpp/base' },
            },
            {
              label: 'C++ Project Code',
              autogenerate: { directory: 'api/cpp/project' },
            },
            {
              label: 'Python Modules',
              autogenerate: { directory: 'api/python' },
            },
          ],
        },
      ],
    }),
  ],
});
