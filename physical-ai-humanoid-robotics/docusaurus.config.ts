import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const config: Config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'From ROS 2 to Vision-Language-Action Robots',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://physical-ai-robotics.github.io',
  baseUrl: '/',

  organizationName: 'physical-ai-robotics',
  projectName: 'physical-ai-humanoid-robotics',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.13.24/dist/katex.min.css',
      type: 'text/css',
      integrity: 'sha384-odtC+0UGzzFL/6PNoE8rX/SPcQDXBJ+uRepguP4QkPCm2LBxH3FA3y+fKSiJ+AmM',
      crossorigin: 'anonymous',
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          showLastUpdateTime: false,
          showLastUpdateAuthor: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    navbar: {
      title: 'Physical AI & Humanoid Robotics',
      logo: {
        alt: 'Physical AI Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'bookSidebar',
          position: 'left',
          label: 'Book',
        },
        {
          to: '/docs/glossary',
          label: 'Glossary',
          position: 'left',
        },
        {
          href: 'https://github.com/physical-ai-robotics/physical-ai-humanoid-robotics',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Book',
          items: [
            { label: 'Introduction', to: '/docs/intro' },
            { label: 'Module 1: ROS 2', to: '/docs/module-1-ros2/what-is-ros2' },
            { label: 'Module 2: Digital Twin', to: '/docs/module-2-digital-twin/what-is-digital-twin' },
            { label: 'Module 3: Isaac', to: '/docs/module-3-isaac/isaac-sim-overview' },
            { label: 'Module 4: VLA', to: '/docs/module-4-vla/what-is-vla' },
          ],
        },
        {
          title: 'Resources',
          items: [
            { label: 'Glossary', to: '/docs/glossary' },
            { label: 'ROS 2 Docs', href: 'https://docs.ros.org/en/humble/' },
            { label: 'NVIDIA Isaac', href: 'https://developer.nvidia.com/isaac-sim' },
            { label: 'Nav2', href: 'https://navigation.ros.org/' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub', href: 'https://github.com/physical-ai-robotics' },
            { label: 'ROS Discourse', href: 'https://discourse.ros.org/' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics. Made by Zohaib Javed. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml', 'markup', 'json', 'csharp', 'cpp'],
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
