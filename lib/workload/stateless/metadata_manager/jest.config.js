module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests/'],
    reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: 'target/report',
        outputName: 'metadataManager.xml',
      },
    ],
  ],
};
