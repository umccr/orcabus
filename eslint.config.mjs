import globals from 'globals';
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  {
    // https://eslint.org/docs/latest/use/configure/ignore
    ignores: [
      '**/build/',
      '**/coverage/',
      '**/*.html',
      '**/.pre-commit-config.yaml',
      '**/buildspec.yml',
      '**/compose.yml',
      '**/docker-compose.yml',
      '**/docker-compose.ci.yml',
      '**/docker-compose.override.sample.yml',
      '**/README.md',
      '**/cdk.out/',
      '**/cdk.json',
      '**/cdk.context.json',
      '**/.yarn/',
      '**/.yarnrc.yml',
      '**/tsconfig.json',
      '**/.local/',
      '**/skel/',
      '**/docs/',
      '**/openapi/',
      '**/shared/',
      'lib/workload/stateless/stacks/*', // FIXME: early days ignore them (microservices) for now
    ],
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.jest,
        Atomics: 'readonly',
        SharedArrayBuffer: 'readonly',
      },

      parser: tseslint.parser,
      ecmaVersion: 'latest',
      sourceType: 'module',

      parserOptions: {
        ecmaFeatures: {
          jsx: true,
          restParams: true,
          spread: true,
        },
      },
    },
  },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  eslintConfigPrettier,
];
