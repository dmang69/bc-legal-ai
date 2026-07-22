# App icons

Place `icon-192.png` and `icon-512.png` here for PWA / mobile installs.

Generate placeholders with any design tool, or:

```bash
# optional: ImageMagick
convert -size 192x192 xc:'#1a2332' -fill white -gravity center -pointsize 28 -annotate 0 'BC' icon-192.png
```

Until icons exist, browsers still allow “Add to Home Screen” with a default icon.
