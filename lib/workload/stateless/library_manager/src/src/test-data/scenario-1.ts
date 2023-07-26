import { DependencyContainer } from 'tsyringe';
import e from '../../dbschema/edgeql-js';
import { Client } from 'edgedb';
import { Logger } from 'pino';

export default async function insertScenario1(dc: DependencyContainer) {
  const edgeDbClient = dc.resolve<Client>('Database');
  const logger = dc.resolve<Logger>('Logger');

  logger.info('inserting scenario 1');
  await e
    .insert(e.metadata.Experiment, {
      identifier: 'Exper1',
      type: 'WTS',
      patients: e.set(
        e.insert(e.metadata.Patient, {
          identifier: 'SUBIDA',
          externalIdentifiers: e.array([
            e.tuple({ system: 'externalSubjectId', value: 'EXTSUBIDA' }),
          ]),
          samples: e.insert(e.metadata.Sample, {
            identifier: 'SAMIDA',
            externalIdentifiers: e.array([
              e.tuple({ system: 'externalSampleId', value: 'SAMIDA-EXTSAMA' }),
            ]),
            assay: 'NebRNA',
            phenotype: 'tumor',
            projectName: 'Alice',
            projectOwner: 'ALICE',
            source: 'FFPE',
            libraries: e.set(
              e.insert(e.metadata.Library, {
                workflow: 'clinical',
                identifier: 'LIB01',
                coverage: 6.0,
                overrideCycles: 'Y151;I8;I8;Y151',
                quality: 'poor',
                runNumber: 'P30',
              }),
              e.insert(e.metadata.Library, {
                workflow: 'clinical',
                identifier: 'LIB04',
                coverage: 6.0,
                overrideCycles: 'Y151;I8;I8;Y151',
                quality: 'poor',
                runNumber: 'P30',
              })
            ),
          }),
        }),
        e.insert(e.metadata.Patient, {
          identifier: 'SUBIDB',
          externalIdentifiers: e.array([
            e.tuple({ system: 'externalSubjectId', value: 'EXTSUBIDB' }),
          ]),
          samples: e.insert(e.metadata.Sample, {
            identifier: 'SAMIDB',
            externalIdentifiers: e.array([
              e.tuple({ system: 'externalSampleId', value: 'EXTSAMB' }),
            ]),
            assay: 'NebRNA',
            phenotype: 'tumor',
            projectName: 'FAKE',
            projectOwner: 'Bob',
            source: 'FFPE',
            libraries: e.set(
              e.insert(e.metadata.Library, {
                workflow: 'clinical',
                identifier: 'LIB02',
                coverage: 6.0,
                overrideCycles: 'Y151;I8;I8;Y151',
                quality: 'poor',
                runNumber: 'P30',
              }),
              e.insert(e.metadata.Library, {
                workflow: 'clinical',
                identifier: 'LIB03',
                coverage: 6.0,
                overrideCycles: 'Y151;I8;I8;Y151',
                quality: 'poor',
                runNumber: 'P30',
              })
            ),
          }),
        })
      ),
    })
    .run(edgeDbClient);
}
