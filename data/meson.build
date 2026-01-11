flatpak_build = get_option('flatpak_build')

desktop_file = flatpak_build ? \
  'io.github.Faugus.subtitle-downloader.desktop' : \
  'subtitle-downloader.desktop'

install_data(
  desktop_file,
  install_dir: get_option('datadir') / 'applications'
)
