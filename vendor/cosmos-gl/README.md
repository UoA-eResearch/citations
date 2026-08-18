# cosmos.gl (vendored dev build with 3D support)

`cosmos.min.js` is a UMD build (global: `Cosmos`) of [cosmos.gl](https://github.com/cosmosgl/graph)
branch **feat/3d-merged** (commit 821528e, 2026-07-13, package version 3.1.0), which adds
`spaceDimensions: 2 | 3` — GPU 3D force simulation with an orbit camera — not yet in an npm release.

Rebuild (or swap to the official release once 3D ships on npm):

```
git clone -b feat/3d-merged https://github.com/cosmosgl/graph
cd graph && npm install && npx vite build --mode umd
cp dist/index.min.js <repo>/vendor/cosmos-gl/cosmos.min.js
```
