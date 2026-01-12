flatpak_build = get_option('flatpak_build')

icon_name = flatpak_build ? 'io.github.Faugus.subtitle-downloader.png' : 'subtitle-downloader.png'

install_data(
  'subtitle-downloader.png',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / '256x256' / 'apps',
  rename: icon_name,
)
