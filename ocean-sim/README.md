# 海洋天空模擬 (GLSL Ocean Simulation)

`index.html` is a single self-contained WebGL2 page: open it in a browser, no build step needed.

- **海洋**: raymarched height field (12 directional wave octaves with deep-water dispersion), Fresnel sky reflection, GGX sun/moon glitter, subsurface tint, whitecaps, and the Earth's curvature for a real horizon.
- **大氣**: single-scattering Rayleigh + Mie + ozone sky, rendered into a lookup table every frame. It lit by both the sun and the moon, so it shows twilight, the Earth's shadow and moonlit sky.
- **太陽 / 月球**: real positions for any date, time and location (low-precision ephemerides, lunar parallax, refraction). The lunar phase and the orientation of its lit side come from the true sun–moon geometry, with Lommel–Seeliger shading, maria and earthshine.
- **星空**: 64 bright stars from the catalogue at J2000 positions with B−V colours, a procedural faint field down to ~6.8 mag and the Milky Way placed on the galactic plane. All of it rotates with local sidereal time, with extinction and twinkling near the horizon.
- **曝光**: auto exposure follows real luminance ratios (sun : full moon : night sky), with a scotopic blue shift at night.

Controls: 時間控制桿 (time of day, with sunrise/sunset/moonrise/moonset marks), 日期控制桿 (day of year, with full/new moon marks), play speed from 1× to 86400×, location presets, waves, camera height, FOV (mouse wheel) and sun/moon display size. Drag to look around, press Space to play or pause, and use ←/→ to step 15 min.
