flatpak_build = get_option('flatpak_build')

desktop_file = flatpak_build ? 'io.github.Faugus.subtitle-downloader.desktop' : 'subtitle-downloader.desktop'

install_data(
  desktop_file,
  install_dir: get_option('datadir') / 'applications'
)

metainfo_file = flatpak_build ? 'io.github.Faugus.subtitle-downloader.metainfo.xml' : 'subtitle-downloader.metainfo.xml'

install_data(
  metainfo_file,
  install_dir: get_option('datadir') / 'metainfo',
)
