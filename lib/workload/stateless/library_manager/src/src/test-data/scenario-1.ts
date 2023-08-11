import { DependencyContainer } from 'tsyringe';
import e from '../../dbschema/edgeql-js';
import { Client } from 'edgedb';
import { Logger } from 'pino';

export default async function insertScenario1(dc: DependencyContainer) {
  const edgeDbClient = dc.resolve<Client>('Database');
  const logger = dc.resolve<Logger>('Logger');

  // logger.info('inserting scenario 1');
  // await e
  //   .insert(e.metadata.Patient, {
  //     identifier: 'SUBIDA',
  //     externalId: e.array([e.tuple({ system: 'externalSubjectId', value: 'EXTSUBIDA' })]),
  //     samples: e.insert(e.metadata.Sample, {
  //       identifier: 'SAMIDA',
  //       externalId: e.array([
  //         e.tuple({ system: 'externalSampleId', value: 'SAMIDA-EXTSAMA' }),
  //       ]),
  //       source: 'FFPE',
  //       libraries: e.set(
  //         e.insert(e.metadata.Library, {
  //           assay: 'NebRNA',
  //           phenotype: 'tumor',
  //           workflow: 'clinical',
  //           identifier: 'LIB01',
  //           coverage: 6.0,
  //           quality: 'poor',
  //         }),
  //         e.insert(e.metadata.Library, {
  //           assay: 'NebRNA',
  //           phenotype: 'tumor',
  //           workflow: 'clinical',
  //           identifier: 'LIB04',
  //           coverage: 6.0,
  //           quality: 'poor',
  //         })
  //       ),
  //     }),
  //   })
  //   .run(edgeDbClient);

  // await e
  //   .insert(e.metadata.Patient, {
  //     identifier: 'SUBIDB',
  //     externalId: e.array([e.tuple({ system: 'externalSubjectId', value: 'EXTSUBIDB' })]),
  //     samples: e.insert(e.metadata.Sample, {
  //       identifier: 'SAMIDB',
  //       externalId: e.array([e.tuple({ system: 'externalSampleId', value: 'EXTSAMB' })]),
  //       source: 'FFPE',
  //       libraries: e.set(
  //         e.insert(e.metadata.Library, {
  //           phenotype: 'tumor',
  //           workflow: 'clinical',
  //           identifier: 'LIB02',
  //           coverage: 6.0,
  //           assay: 'NebRNA',
  //           quality: 'poor',
  //         }),
  //         e.insert(e.metadata.Library, {
  //           phenotype: 'tumor',
  //           workflow: 'clinical',
  //           identifier: 'LIB03',
  //           coverage: 6.0,
  //           assay: 'NebRNA',
  //           quality: 'poor',
  //         })
  //       ),
  //     }),
  //   })
  //   .run(edgeDbClient);
}
