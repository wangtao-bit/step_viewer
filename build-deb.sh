#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
name=local-step-viewer
app="$stage/usr/share/$name"
mkdir -p "$stage/DEBIAN" "$app/assets" "$stage/usr/bin" "$root/dist"
install -m 644 "$root/packaging/control" "$stage/DEBIAN/control"
install -m 644 "$root"/*.py "$app/"
install -m 644 "$root"/assets/* "$app/assets/"
chmod 755 "$app/viewer.py"
ln -s "../share/$name/viewer.py" "$stage/usr/bin/$name"
desktop="$stage/usr/share/applications/$name.desktop"
install -Dm644 "$root/local-step-viewer.desktop" "$desktop"
install -Dm644 "$root/assets/app.svg" "$stage/usr/share/icons/hicolor/scalable/apps/$name.svg"
install -Dm644 "$root/model-step.xml" "$stage/usr/share/mime/packages/$name.xml"
dpkg-deb --root-owner-group --build "$stage" "$root/dist/"
