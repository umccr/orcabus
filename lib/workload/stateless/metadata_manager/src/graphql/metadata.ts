// WIP - The idea is to have graphql schema for other queries
// See notes in /src/api/routes/graphql-routes.ts

export const metadataSchema = `#graphql
enum WorkflowTypes {
  clinical
  research
  qc
  control
  bcl
  manual
}

type Library {
  id: ID!
  orcaBusId: String!
  internalId: String!
  externalId: String

  assay: String
  coverage: Float
  phenotype: String
  quality: String
  type: String
  workflow: WorkflowTypes
  specimen: Specimen
}

type Specimen {
  id: ID!
  orcaBusId: String!
  internalId: String!
  externalId: String
  
  source: String
  
  libraries: [Library!]
  subject: Subject
}

type Subject {
  id: ID!
  orcaBusId: String!
  internalId: String!
  externalId: String
  specimens: [Specimen]
}

# Query function
type Query {
  getLibrary: [Library]
}
`;
