import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Start Learning - Read the Book
          </Link>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  description: string;
  link: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Module 1: ROS 2',
    description: 'Master the Robot Operating System - nodes, topics, services, URDF, and Python-based robot control.',
    link: '/docs/module-1-ros2/what-is-ros2',
  },
  {
    title: 'Module 2: Digital Twin',
    description: 'Build virtual replicas with Gazebo and Unity. Create physics-accurate simulations for testing.',
    link: '/docs/module-2-digital-twin/what-is-digital-twin',
  },
  {
    title: 'Module 3: NVIDIA Isaac',
    description: 'GPU-accelerated perception with Isaac Sim, Visual SLAM, and Nav2 for intelligent navigation.',
    link: '/docs/module-3-isaac/isaac-sim-overview',
  },
  {
    title: 'Module 4: VLA Systems',
    description: 'Create autonomous robots using voice commands, LLM planning, and manipulation control.',
    link: '/docs/module-4-vla/what-is-vla',
  },
];

function Feature({title, description, link}: FeatureItem) {
  return (
    <div className={clsx('col col--3')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
        <Link className="button button--primary button--sm" to={link}>
          Start Module
        </Link>
      </div>
    </div>
  );
}

function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Physical AI & Humanoid Robotics"
      description="Complete guide from ROS 2 to Vision-Language-Action autonomous robots">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <section style={{padding: '2rem 0', textAlign: 'center', background: 'var(--ifm-background-surface-color)'}}>
          <div className="container">
            <Heading as="h2">What You'll Build</Heading>
            <p style={{maxWidth: '800px', margin: '0 auto 2rem', fontSize: '1.1rem'}}>
              By the end of this book, you'll create an autonomous humanoid robot that can understand voice commands,
              navigate environments, perceive objects, and execute manipulation tasks.
            </p>
            <div style={{display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap'}}>
              <div style={{padding: '1rem', borderRadius: '8px', background: 'var(--ifm-color-primary-lightest)', minWidth: '150px'}}>
                <strong>Voice Input</strong>
                <p style={{margin: '0.5rem 0 0', fontSize: '0.9rem'}}>Whisper ASR</p>
              </div>
              <div style={{padding: '1rem', borderRadius: '8px', background: 'var(--ifm-color-primary-lightest)', minWidth: '150px'}}>
                <strong>AI Planning</strong>
                <p style={{margin: '0.5rem 0 0', fontSize: '0.9rem'}}>LLM-based</p>
              </div>
              <div style={{padding: '1rem', borderRadius: '8px', background: 'var(--ifm-color-primary-lightest)', minWidth: '150px'}}>
                <strong>Navigation</strong>
                <p style={{margin: '0.5rem 0 0', fontSize: '0.9rem'}}>Nav2 Stack</p>
              </div>
              <div style={{padding: '1rem', borderRadius: '8px', background: 'var(--ifm-color-primary-lightest)', minWidth: '150px'}}>
                <strong>Manipulation</strong>
                <p style={{margin: '0.5rem 0 0', fontSize: '0.9rem'}}>Pick & Place</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
