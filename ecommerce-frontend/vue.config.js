const CompressionPlugin = require('compression-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  publicPath: '/',
  productionSourceMap: false,
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  pluginOptions: {
    compression: {
      gzip: true
    }
  },
  configureWebpack: () => {
    const config = {
      optimization: {
        splitChunks: {
          chunks: 'all',
          maxInitialRequests: 8,
          minSize: 20000,
          cacheGroups: {
            vendors: {
              test: /[\\/]node_modules[\\/]/,
              name: 'chunk-vendors',
              priority: -10
            },
            elementPlus: {
              test: /[\\/]node_modules[\\/]element-plus[\\/]/,
              name: 'chunk-element-plus',
              priority: 20,
              reuseExistingChunk: true
            },
            commons: {
              name: 'chunk-commons',
              minChunks: 2,
              priority: -20,
              reuseExistingChunk: true
            }
          }
        }
      },
      plugins: []
    };

    if (process.env.NODE_ENV === 'production') {
      config.plugins.push(
        new CompressionPlugin({
          algorithm: 'brotliCompress',
          test: /\.(js|css|html|svg)$/,
          threshold: 10240,
          minRatio: 0.8
        })
      );
    }

    if (process.env.ANALYZE === 'true') {
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: 'bundle-report.html'
        })
      );
    }

    return config;
  },
  chainWebpack: (config) => {
    config.plugins.delete('prefetch');
    config.plugin('html').tap((args) => {
      args[0].title = 'Ecommerce Admin';
      return args;
    });
  }
};

