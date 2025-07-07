import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.{js,mjs,cjs,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        global: 'readonly',
        router: 'readonly'
      }
    },
    rules: {
      // Make rules less strict for development
      'no-unused-vars': 'off',
      'no-console': 'off',
      'no-undef': 'off',
      'vue/multi-word-component-names': 'off'
    }
  },
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      '*.config.js'
    ]
  }
]
