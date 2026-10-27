import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// GitHub Pages serves the site under /<repo>/; the workflow sets BASE_PATH.
const base = (process.env.BASE_PATH || '/').replace(/\/+$/, '');

// Hand-written pages link with root-relative hrefs ("/pipeline/"); prefix them with the base path.
function rehypeBase() {
  const walk = (n) => {
    if (n.type === 'raw') n.value = n.value.replace(/href="\/(?!\/)/g, `href="${base}/`);
    const href = n.properties?.href;
    if (n.tagName === 'a' && typeof href === 'string' && /^\/(?!\/)/.test(href) && !href.startsWith(base + '/')) {
      n.properties.href = base + href;
    }
    n.children?.forEach(walk);
  };
  return walk;
}

export default defineConfig({
  site: 'https://fbientrigo.github.io',
  base: base || '/',
  markdown: { remarkPlugins: [remarkMath], rehypePlugins: [rehypeKatex, rehypeBase] },
  integrations: [
    starlight({
      title: 'ATLAS // DIHIGGS',
      description: 'Documentation and API reference for the 2HDM di-Higgs and LLP recast workspace.',
      customCss: ['katex/dist/katex.min.css', './src/styles/wired.css'],
      social: { github: 'https://github.com/fbientrigo/atlas_dihiggs' },
      pagination: false,
      expressiveCode: { themes: ['min-light', 'min-dark'], defaultProps: { frame: 'none' } },
      sidebar: [
        {
          label: '[00] Overview',
          items: [
            { label: 'Introduction', link: '/' },
            { label: 'Getting started', link: '/getting-started/' },
            { label: 'Pipeline', link: '/pipeline/' },
          ],
        },
        {
          label: '[01] Modules',
          items: [
            { label: 'Overview', link: '/modules/' },
            { label: 'dihiggs', link: '/modules/dihiggs/' },
            { label: 'dihiggs_ufo', link: '/modules/dihiggs-ufo/' },
            { label: 'dihiggs_hep_cross', link: '/modules/dihiggs-hep-cross/' },
            { label: 'dihiggs_llp_recast', link: '/modules/dihiggs-llp-recast/' },
            { label: 'dihiggs_boundary', link: '/modules/dihiggs-boundary/' },
            { label: 'recast_viewer', link: '/modules/recast-viewer/' },
          ],
        },
        {
          label: '[02] Governance',
          items: [
            { label: 'Physics authority', link: '/authority/' },
            { label: 'Data lake', link: '/lake/' },
          ],
        },
        {
          label: '[03] API reference',
          items: [
            { label: 'Index & coverage', link: '/api/' },
            { label: '2HDMC · C++ · base', collapsed: true, autogenerate: { directory: 'api/cpp/base/2hdmc' } },
            { label: 'HiggsTools · C++ · base', collapsed: true, autogenerate: { directory: 'api/cpp/base/higgstools' } },
            { label: 'dihiggs · C++', collapsed: true, autogenerate: { directory: 'api/cpp/project/dihiggs' } },
            { label: 'boundary · C++', collapsed: true, autogenerate: { directory: 'api/cpp/project/boundary' } },
            { label: 'hep_cross · C++', collapsed: true, autogenerate: { directory: 'api/cpp/project/hep_cross' } },
            { label: 'llp_recast · C++', collapsed: true, autogenerate: { directory: 'api/cpp/project/llp_recast' } },
            { label: 'dihiggs · Python', collapsed: true, autogenerate: { directory: 'api/python/dihiggs' } },
            { label: 'boundary · Python', collapsed: true, autogenerate: { directory: 'api/python/dihiggs-boundary' } },
            { label: 'hep_cross · Python', collapsed: true, autogenerate: { directory: 'api/python/dihiggs-hep-cross' } },
            { label: 'llp_recast · Python', collapsed: true, autogenerate: { directory: 'api/python/dihiggs-llp-recast' } },
            { label: 'ufo · Python', collapsed: true, autogenerate: { directory: 'api/python/dihiggs-ufo' } },
            { label: 'recast_viewer · Python', collapsed: true, autogenerate: { directory: 'api/python/recast-viewer' } },
          ],
        },
      ],
    }),
  ],
});
