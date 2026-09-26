# Third-party components and data

This file records the provenance retained with bundled components. Their notices and data metadata remain separate from the application's own license.

- `Skills/amap-jsapi` and `Skills/amap-lbs`: provider references credit Gaode / amap and contain their MIT metadata. Optional usage-reporting instructions have been removed from the local WebService guide.
- `Skills/weather`: Open-Meteo reference material and the `open_meteo_skill` client are retained with their source metadata. The OpenWebUI adapter credits [anzejing/open-meteo-skill](https://github.com/anzejing/open-meteo-skill). Its package description now points to the included `SKILL.md`.
- The FlyAI, CarInfo, OpenTripMap and Open Charge Map references retain provider attribution, terms links and data-format descriptions in their respective `Skills/` directories.
- [The McLaren asset note](frontend/public/models/MCLAREN_LICENSE.md) records the supplied archive and processing history. The supplied asset had no license file; no replacement license is assigned to it here.
- `frontend/scripts/copy-draco.mjs` generates a decoder notice crediting Google Inc. under Apache-2.0 when dependencies are installed. Its notice text is retained.
- Dependency versions, source URLs, integrity values and license metadata remain in `frontend/package-lock.json`.

## Runtime data attribution

Provider adapters attach source URLs, retrieval times and available license metadata to results. Preserve these fields when changing views or exports. The available sources include AMap, Open-Meteo, wttr.in, MET Norway, 7Timer, OpenTripMap, OpenStreetMap, FlyAI, Bitefu, AutoSeeker, OpenEV Data, AppByte Fleet Catalog and CarNewsChina. Optional rail, flight and oil-price adapters retain their own source links. No production database, real-user history or provider credentials are included.

Synthetic examples and the range replay dataset retain their simulation labels and format versions; they are not real vehicle telemetry.
