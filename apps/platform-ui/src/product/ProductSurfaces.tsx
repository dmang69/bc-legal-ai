import type { DeveloperBlueprint, ExecutiveBrief, ProductBlueprint } from "./types";

type ProductSurfacesProps = Readonly<{
  product: ProductBlueprint;
  executive: ExecutiveBrief;
  developer: DeveloperBlueprint;
}>;

function ListCard({ title, items }: Readonly<{ title: string; items: string[] }>) {
  return (
    <article className="product-card">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </article>
  );
}

function ExecutiveSurface({ product, executive }: Readonly<{ product: ProductBlueprint; executive: ExecutiveBrief }>) {
  return (
    <section className="product-surface" aria-label="Executive legal intelligence surface">
      <div className="product-hero">
        <p className="eyebrow">Executive Edition</p>
        <h1>{executive.headline}</h1>
        <p className="hero-subtitle">{executive.subheadline}</p>
        <p>{product.elevator_pitch}</p>
        <div className="cta-row" aria-label="Executive calls to action">
          <button type="button">{executive.primary_cta}</button>
          <button className="secondary" type="button">{executive.secondary_cta}</button>
        </div>
      </div>

      <div className="brief-grid">
        <article className="product-card wide">
          <h2>Problem Statement</h2>
          <p>{executive.problem_statement}</p>
        </article>
        <ListCard title="Business Outcomes" items={executive.business_outcomes} />
        <ListCard title="Executive Use Cases" items={executive.use_cases} />
        <ListCard title="KPI Suggestions" items={executive.kpis} />
        <ListCard title="Strategic Benefits" items={product.strategic_benefits} />
      </div>
    </section>
  );
}

function DeveloperSurface({ product, developer }: Readonly<{ product: ProductBlueprint; developer: DeveloperBlueprint }>) {
  const sampleJson = JSON.stringify(developer.sample_legal_requirement, null, 2);

  return (
    <section className="product-surface" aria-label="Developer legal implementation surface">
      <div className="product-hero developer">
        <p className="eyebrow">Developer Edition</p>
        <h1>Build-ready legal requirements for compliant systems</h1>
        <p className="hero-subtitle">{developer.architecture_overview}</p>
        <p>{product.positioning_statement}</p>
      </div>

      <div className="architecture-stack">
        {developer.layers.map((layer) => (
          <article className="product-card" key={layer.name}>
            <h3>{layer.name}</h3>
            <ul>
              {layer.components.map((component) => <li key={component}>{component}</li>)}
            </ul>
          </article>
        ))}
      </div>

      <div className="brief-grid">
        <ListCard title="Service Map" items={developer.service_map} />
        <ListCard title="Output Formats" items={developer.output_formats} />
        <ListCard title="Security Architecture" items={developer.security_architecture} />
        <ListCard title="AI Requirements" items={developer.ai_requirements} />
      </div>

      <article className="product-card wide code-card">
        <h2>Example JSON legal requirement set</h2>
        <pre>{sampleJson}</pre>
      </article>
    </section>
  );
}

function ModuleSurface({ product }: Readonly<{ product: ProductBlueprint }>) {
  return (
    <section className="product-surface" aria-label="Platform module surface">
      <div className="product-hero modules">
        <p className="eyebrow">Platform Modules</p>
        <h1>{product.product_name}</h1>
        <p className="hero-subtitle">{product.one_line_description}</p>
        <p className="safeguard">{product.messaging_safeguard}</p>
      </div>
      <div className="module-grid">
        {product.core_modules.map((module) => (
          <article className="product-card" key={module.id}>
            <h3>{module.title}</h3>
            <p>{module.description}</p>
          </article>
        ))}
      </div>
      <div className="brief-grid">
        {Object.entries(product.feature_tiers).map(([tier, items]) => (
          <ListCard key={tier} title={tier.replace("_", " ").toUpperCase()} items={items} />
        ))}
      </div>
    </section>
  );
}

export function ProductSurfaces({ product, executive, developer }: ProductSurfacesProps) {
  return (
    <div className="product-layout">
      <ExecutiveSurface product={product} executive={executive} />
      <DeveloperSurface product={product} developer={developer} />
      <ModuleSurface product={product} />
    </div>
  );
}
