/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const glob = require('glob');
const path = require('path');
const webpack = require('webpack');
const FileManagerPlugin = require('filemanager-webpack-plugin');

const GLOB_OPTIONS = {
  ignore: ['**/*test.ts', '**/*test.js', '**/testing_utils.ts']
};

/**
 * WebPack config generator function.
 *
 * @param {?object=} env Environment variables for WebPack to use.
 * @return {!object} WebPack config definition.
 */
module.exports = (env = {}) => {
  const isProd = !!env.production;
  const isDev = !isProd;
  console.log('⭐️ Packing web...', env);

  const buildStr = env.build || '';
  const toBuild = buildStr.split(',').filter(x => x.length > 0);

  /**
  * File groups to include in the build.
  */
  const core = glob.sync(resolveDir('../core/**/*.ts'), GLOB_OPTIONS);
  const elements = glob.sync(resolveDir('../elements/**/*.ts'), GLOB_OPTIONS);
  const lib = glob.sync(resolveDir('../lib/**/*.ts'), GLOB_OPTIONS);
  const modules = glob.sync(resolveDir('../modules/**/*.ts'), GLOB_OPTIONS);
  const services = glob.sync(resolveDir('../services/**/*.ts'), GLOB_OPTIONS);

  /**
  * Make the default entry and FileManagerPlugin params objects, which will
  * determine which output bundles to build and where to move them to
  */
  const entry = {
    default: [
      resolveDir('../main.ts'),
      ...core,
      ...elements,
      ...lib,
      ...modules,
      ...services,
    ],
  };
  const fileManagerParams = {
    onEnd: {
      copy: [{
        source: resolveDir('../static'),
        destination: resolveDir('../build/default/static')
      }],
      move: [],
    },
  };

  toBuild.forEach(path => {
    const splitPath = path.split('/');
    const moduleName = splitPath[splitPath.length -1];
    entry[moduleName] = resolveDir(`../../${path}/main.ts`);

    fileManagerParams.onEnd.copy.push({
      source: resolveDir('../static'),
      destination: resolveDir(`../../${path}/build/static`)
    });
    fileManagerParams.onEnd.move.push({
      source: resolveDir(`../build/${moduleName}/main.js`),
      destination: resolveDir(`../../${path}/build/main.js`)
    });

    fileManagerParams.onEnd.delete = fileManagerParams.onEnd.delete || [];
    fileManagerParams.onEnd.delete.push(resolveDir(`../build/${moduleName}`));
  });

  return {
    mode: isDev ? 'development' : 'production',
    devtool: isDev ? 'inline-source-map' : 'none',
    module: {
      rules: [
        {
          test: /(\.ts$|\.js$)/,
          exclude: [/node_modules/, '/test.ts$/', '/umap_worker/'],
          use: [
            {
              loader: 'ts-loader',
              options: {
                compilerOptions: {
                  target: 'es6',
                  noImplicitAny: false,
                },
              },
            },
          ],
        },
        // Load the lit-element css files
        {
          test: /\.css$/i,
          loader: resolveDir('./lit-css-loader.js'),
        },
      ],
    },
    resolve: {
      modules: ['node_modules'],
      extensions: ['.ts', '.js'],
    },
    entry,
    output: {
      filename: '[name]/main.js',
      path: resolveDir('../build'),
    },
    plugins: [
      new webpack.DefinePlugin({
        PRODUCTION: isProd,
      }),
      new FileManagerPlugin(fileManagerParams)
    ],
    watch: isDev,
  };
};

/**
 * Convenience wrapper for path.resolve().
 *
 * @param {string} relativeDir path to a directory relative to
 *    lit_nlp/client/webpack.
 *
 * @return {string} Fully qualified path.
 */
function resolveDir(relativeDir) {
  return path.resolve(__dirname, relativeDir);
}
