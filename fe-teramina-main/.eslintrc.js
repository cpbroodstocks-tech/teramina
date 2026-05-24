module.exports = {
  env: {
    browser: true,
    commonjs: true,
    es6: true,
    jest: true,
    node: true
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:jsx-a11y/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaFeatures: {
      jsx: true
    },
    ecmaVersion: "latest",
    sourceType: "module"
  },
  plugins: [
    "import",
    "prettier",
    "@typescript-eslint"
  ],
  root: true,
  rules: {
    "no-async-promise-executor": "off",
    "react-hooks/set-state-in-effect": "off",
    "react/display-name": "off",
    "react-hooks/exhaustive-deps": "off",
    "react-hooks/refs": "off",
    "react/no-unknown-property": "off",
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off",
    "jsx-quotes": [
      "warn",
      "prefer-double"
    ],
    "max-len": [
      "warn",
      {
        "code": 170,
        "ignoreTemplateLiterals": true,
        "ignoreStrings": true
      }
    ],
    "no-unused-vars": "error",
    "no-console": "error",
    "no-restricted-syntax": [
      "error",
      {
        "selector": "CallExpression[callee.object.name='console'][callee.property.name!=/^(log|warn|error|info|trace)$/]",
        "message": "Unexpected property on console object was called"
      }
    ],
    indent: [
      "error",
      2
    ],
    quotes: [
      "warn",
      "double"
    ]
  },
  overrides: [
    {
      files: ["**/*.ts", "**/*.tsx"],
      rules: {
        "no-unused-vars": "off",
        "@typescript-eslint/no-unused-vars": "error"
      }
    },
    {
      files: ["src/tests/**/*"],
      extends: ["plugin:testing-library/react"]
    }
  ],
  settings: {
    react: {
      version: "detect"
    }
  }
};
