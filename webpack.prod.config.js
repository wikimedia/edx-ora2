process.env.BABEL_ENV = 'production';
process.env.NODE_ENV = 'production';

const { createConfig } = require('@edx/frontend-build');
const { mergeWithRules } = require('webpack-merge');

const webpack = require('webpack');
const path = require('path');
const Dotenv = require('dotenv-webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const PostCssAutoprefixerPlugin = require('autoprefixer');
const CssNano = require('cssnano');

// Get base config from edx-platform
let config = createConfig('webpack-prod');

// Modify CSS processing rules (remove PostCssRtlPlugin)
const modifiedCssRule = {
  module: {
    rules: [
      {
        test: /(.scss|.css)$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader', // translates CSS into CommonJS
            options: {
              sourceMap: true,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              plugins: () => [
                PostCssAutoprefixerPlugin({ grid: true }),
                CssNano(),
              ],
            },
          },
          'resolve-url-loader',
          {
            loader: 'sass-loader', // compiles Sass to CSS
            options: {
              sourceMap: true,
              sassOptions: {
                includePaths: [
                  path.join(process.cwd(), 'node_modules'),
                  path.join(process.cwd(), 'src'),
                ],
              },
            },
          },
        ],
      },
    ],
  },
};

// Merge back to configuration
config = mergeWithRules({
  module: {
    rules: {
      test: 'match',
      use: 'replace',
    },
  },
})(config, modifiedCssRule);

Object.assign(config, {
  entry: {
    'openassessment-lms': path.resolve(process.cwd(), 'openassessment/xblock/static/js/src/lms_index.js'),
    'openassessment-studio': path.resolve(process.cwd(), 'openassessment/xblock/static/js/src/studio_index.js'),
    'openassessment-rtl': path.resolve(process.cwd(), 'openassessment/xblock/static/sass/openassessment-rtl.scss'),
    'openassessment-ltr': path.resolve(process.cwd(), 'openassessment/xblock/static/sass/openassessment-ltr.scss'),
    'openassessment-editor-textarea': path.resolve(process.cwd(), 'openassessment/xblock/static/js/src/lms/editors/oa_editor_textarea.js'),
    'openassessment-editor-tinymce': path.resolve(process.cwd(), 'openassessment/xblock/static/js/src/lms/editors/oa_editor_tinymce.js'),
  },
  output: {
    path: path.resolve(process.cwd(), 'openassessment/xblock/static/dist'),
  },
  optimization: {},
  plugins: [
    new Dotenv({
      path: path.resolve(process.cwd(), '.env'),
      systemvars: true,
    }),
    new MiniCssExtractPlugin({
      filename: '[name].css',
    }),
    new webpack.ProvidePlugin({
      Backgrid: path.resolve(path.join(__dirname, 'openassessment/xblock/static/js/lib/backgrid/backgrid'))
    }),
  ],
});

config.resolve.modules = ['node_modules'].concat(
  path.resolve(__dirname, 'openassessment/xblock/static/js/src'),
);

module.exports = config;
