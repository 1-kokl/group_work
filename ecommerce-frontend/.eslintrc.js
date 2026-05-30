module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true
  },
  extends: ['plugin:vue/vue3-essential', '@vue/standard'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module'
  },
  rules: {
    semi: 'off',
    'space-before-function-paren': 'off',
    'no-multiple-empty-lines': 'off',
    'vue/multi-word-component-names': 'off',
    'no-unused-vars': 'off'
  }
};


