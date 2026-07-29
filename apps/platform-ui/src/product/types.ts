export type CoreModule = {
  id: string;
  title: string;
  description: string;
};

export type ProductBlueprint = {
  product_name: string;
  tagline: string;
  one_line_description: string;
  elevator_pitch: string;
  vision: string;
  positioning_statement: string;
  messaging_safeguard: string;
  audiences: Record<string, string[]>;
  ideal_customers: string[];
  strategic_benefits: string[];
  core_modules: CoreModule[];
  key_features: string[];
  feature_tiers: Record<string, string[]>;
};

export type ExecutiveBrief = {
  headline: string;
  subheadline: string;
  primary_cta: string;
  secondary_cta: string;
  problem_statement: string;
  solution: string[];
  business_outcomes: string[];
  use_cases: string[];
  kpis: string[];
};

export type ArchitectureLayer = {
  name: string;
  components: string[];
};

export type DeveloperBlueprint = {
  architecture_overview: string;
  layers: ArchitectureLayer[];
  service_map: string[];
  api_domains: Record<string, string[]>;
  output_formats: string[];
  sample_legal_requirement: Record<string, unknown>;
  security_architecture: string[];
  ai_requirements: string[];
};
