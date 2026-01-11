project(
  'subtitle-downloader',
  version: '1.0.0',
  meson_version: '>=1.2.0',
  license: 'MIT',
  license_files: 'LICENSE',
)

subdir('data')
subdir('assets')

install_data(
  'subtitle-downloader.py',
  rename: [
    'subtitle-downloader',
  ],
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('bindir'),
)

install_data(
  'LICENSE',
  install_dir: get_option('datadir') / 'licenses' / meson.project_name(),
)
